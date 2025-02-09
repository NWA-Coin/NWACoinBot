import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import logging
import sys
from datetime import datetime, timedelta
import asyncio
import time  # Add missing time import
from roast_generator import generate_roast
from meme_generator import generate_meme
from price_chart import get_lux_price_history

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger('discord_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    logger.error("No Discord token found in environment variables!")
    exit(1)

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.guilds = True

class PersistentBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            description='LUX Roast Bot - Use !help to see available commands'
        )
        self.last_heartbeat = datetime.now()
        self.heartbeat_interval = timedelta(minutes=5)
        self.start_time = datetime.now()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 50
        self.heartbeat_check_task = None  # Add task reference

    async def setup_hook(self):
        """Called when the bot is first setting up"""
        # Start heartbeat check as a background task
        self.heartbeat_check_task = self.heartbeat_check.start()
        logger.info("Bot setup completed, heartbeat check started")

    @commands.command(name='roast', help='Get a savage roast about LUX')
    async def roast(self, ctx):
        """Generate a roast about LUX."""
        try:
            logger.info(f"Roast command received from {ctx.author}")
            roast = generate_roast()
            await ctx.send(roast)
            logger.info("Roast command completed successfully")
        except Exception as e:
            logger.error(f"Error in roast command: {str(e)}")
            await ctx.send("❌ Failed to generate roast. Please try again!")

    @commands.command(name='meme', help='Generate a savage meme with current LUX price')
    async def meme(self, ctx):
        """Generate and send a meme about LUX."""
        try:
            logger.info(f"Meme command received from {ctx.author}")
            await ctx.send("Generating price chart... Please wait...")

            meme_result = generate_meme()
            if meme_result and meme_result.endswith('.png'):
                logger.info("Successfully generated meme image")
                with open(meme_result, 'rb') as f:
                    await ctx.send(file=discord.File(f))
                os.remove(meme_result)
                logger.info("Meme sent and temp file cleaned up")
            else:
                logger.warning(f"Meme generation returned unexpected result: {meme_result}")
                await ctx.send(meme_result)
        except Exception as e:
            logger.error(f"Error in meme command: {str(e)}")
            await ctx.send("❌ Failed to generate meme. Please try again!")

    @commands.command(name='crash', help='Show how much LUX crashed since NWA started shorting')
    async def crash(self, ctx):
        """Show LUX price crash stats."""
        try:
            logger.info(f"Crash command received from {ctx.author}")
            await ctx.send("Fetching price data... Please wait...")

            dates, prices = get_lux_price_history()
            if not dates or not prices:
                logger.error("Failed to get price data")
                await ctx.send("❌ Failed to get price data. Probably rugpulled to zero! 💀")
                return

            current_price = prices[-1]
            entry_price = 0.015
            crash_percent = ((entry_price - current_price) / entry_price) * 100

            message = f"💥 LUX CRASH UPDATE 💥\n"
            message += f"NWA Entry: ${entry_price:.4f}\n"
            message += f"Current Price: ${current_price:.8f}\n"
            message += f"Crashed: {crash_percent:.2f}% 📉\n"
            message += "NWA KEEPS WINNING! 🔥 TINO KEEPS CRYING! 😭"

            await ctx.send(message)
            logger.info(f"Crash command completed successfully. Current price: ${current_price:.8f}")
        except Exception as e:
            logger.error(f"Error in crash command: {str(e)}")
            await ctx.send("❌ Failed to get crash stats. Probably as dead as Tino's reputation!")

    @tasks.loop(minutes=1)
    async def heartbeat_check(self):
        """Check bot's connection status and reconnect if needed"""
        try:
            if datetime.now() - self.last_heartbeat > self.heartbeat_interval:
                logger.warning("Heartbeat check failed, attempting to reconnect...")
                await self.reconnect_bot()
            else:
                logger.debug("Heartbeat check passed")
        except Exception as e:
            logger.error(f"Error in heartbeat check: {str(e)}")

    async def reconnect_bot(self):
        """Attempt to reconnect the bot"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached, waiting 30 minutes before resetting counter")
            try:
                await asyncio.sleep(1800)  # Wait 30 minutes
                self.reconnect_attempts = 0
                logger.info("Reset reconnection attempts counter")
            except Exception as e:
                logger.error(f"Error during reconnection wait: {str(e)}")
            return

        try:
            self.reconnect_attempts += 1
            logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")

            # Close existing connection if any
            try:
                await self.close()
            except Exception as close_error:
                logger.warning(f"Error closing existing connection: {str(close_error)}")

            # Attempt to start new connection
            await self.start(TOKEN)
            self.last_heartbeat = datetime.now()
            logger.info("Reconnection successful")
            self.reconnect_attempts = 0  # Reset counter on successful reconnection
        except Exception as e:
            logger.error(f"Failed to reconnect: {str(e)}")
            # Calculate backoff time
            backoff_time = min(300, 60 * self.reconnect_attempts)
            logger.info(f"Waiting {backoff_time} seconds before next attempt")
            await asyncio.sleep(backoff_time)

    async def on_ready(self):
        """Called when the bot is ready."""
        try:
            self.last_heartbeat = datetime.now()
            uptime = datetime.now() - self.start_time
            logger.info(f'Logged in as {self.user.name}')
            logger.info(f'Bot ID: {self.user.id}')
            logger.info(f'Bot uptime: {uptime}')
            logger.info('Bot is ready!')

            # Print invite link
            logger.info('\nInvite link:')
            logger.info(f'https://discord.com/api/oauth2/authorize?client_id={self.user.id}&permissions=2048&scope=bot%20applications.commands')
        except Exception as e:
            logger.error(f"Error in on_ready: {str(e)}")

    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        try:
            if isinstance(error, commands.CommandNotFound):
                await ctx.send("❌ Command not found! Use `!help` to see available commands.")
            elif isinstance(error, commands.MissingPermissions):
                await ctx.send("❌ I don't have permission to do that!")
            else:
                logger.error(f"Command error: {str(error)}")
                await ctx.send("❌ An error occurred. Please try again!")
        except Exception as e:
            logger.error(f"Error handling command error: {str(e)}")

# Create single bot instance
bot = PersistentBot()

if __name__ == "__main__":
    while True:
        try:
            logger.info("Starting bot...")
            bot.run(TOKEN, log_handler=None)
        except discord.LoginFailure:
            logger.error("Failed to login. Invalid token!")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Bot crashed: {str(e)}")
            logger.info("Attempting to restart in 60 seconds...")
            time.sleep(60)
            continue