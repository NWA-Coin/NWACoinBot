import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys
import time
import asyncio
from datetime import datetime, timedelta
from meme_generator import generate_meme
from roast_generator import generate_roast
from price_chart import get_lux_price_history

# Set up logging with a single handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('discord_bot')

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    logger.error("No Discord token found!")
    exit(1)

# Bot setup with enhanced reconnect settings
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    reconnect=True,
    case_insensitive=True,
    max_messages=10000,  # Increase message cache
    chunk_guilds_at_startup=False,  # Faster startup
    heartbeat_timeout=150.0  # Increased heartbeat timeout
)

# Remove default help command
bot.remove_command('help')

@bot.event
async def on_ready():
    """Called when the bot successfully connects/reconnects"""
    logger.info(f'Logged in as {bot.user.name} ($LUXSUX)')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info('Bot is ready!')
    logger.info('Available commands: !help, !roast, !meme, !crash')

    # Ensure only one keep_alive task runs
    for task in asyncio.all_tasks(bot.loop):
        if task.get_name() == 'keep_alive':
            return

    # Start keep-alive loop if not already running
    keep_alive_task = bot.loop.create_task(keep_alive(), name='keep_alive')
    logger.info("Started keep-alive task")


async def keep_alive():
    """Keep-alive loop to maintain bot connection"""
    logger.info("Starting keep-alive loop")  # Added logging
    while True:
        try:
            if not bot.is_closed():
                logger.info("Keep-alive heartbeat: Bot is active")  # Enhanced logging
                await bot.change_presence(
                    activity=discord.Game(name="!help | Roasting LUX"),
                    status=discord.Status.online  # Explicitly set online status
                )
            else:
                logger.warning("Keep-alive detected closed connection, attempting to reconnect")
            await asyncio.sleep(30)  # Heartbeat every 30 seconds
        except Exception as e:
            logger.error(f"Error in keep-alive loop: {str(e)}")
            await asyncio.sleep(5)  # Wait before retry

@bot.event
async def on_resumed():
    """Log when the bot resumes a session after disconnect"""
    logger.info("Bot resumed connection")
    # Ensure keep-alive task is running
    for task in asyncio.all_tasks(bot.loop):
        if task.get_name() == 'keep_alive':
            break
    else:
        bot.loop.create_task(keep_alive())

@bot.event
async def on_disconnect():
    """Log disconnection and attempt immediate reconnect"""
    logger.warning("Bot disconnected. Attempting to reconnect...")
    await asyncio.sleep(1)  # Brief delay before reconnect attempt

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle any uncaught exceptions"""
    logger.error(f'Error in {event}:')
    logger.exception('Traceback:')

@bot.event
async def on_command(ctx):
    """Log when commands are used"""
    logger.info(f'Command "{ctx.command.name}" used by {ctx.author} in {ctx.guild}')
    # Ensure bot is online when processing commands
    await bot.change_presence(
        activity=discord.Game(name="!help | Roasting LUX"),
        status=discord.Status.online
    )

@bot.event
async def on_message(message):
    """Log all message events for debugging command handling"""
    if message.author == bot.user:
        return

    logger.info(f"Message received: {message.content} from {message.author} in {message.guild}")

    # Check if message starts with command prefix
    if message.content.startswith(bot.command_prefix):
        logger.info(f"Command detected: {message.content}")

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Command on cooldown. Try again in {error.retry_after:.1f}s")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use !help to see available commands.")
    else:
        logger.error(f'Error in command "{ctx.command}": {str(error)}')
        await ctx.send("❌ Command failed! Try !help to see available commands.")

async def update_bot_status():
    """Update bot status to online with activity"""
    await bot.change_presence(
        activity=discord.Game(name="!help | Roasting LUX"),
        status=discord.Status.online
    )

@bot.command(name='roast')
@commands.cooldown(1, 3, commands.BucketType.user)  # Rate limit: 1 use per 3 seconds per user
async def roast(ctx):
    """Generate a savage roast"""
    logger.info(f'Executing roast command for {ctx.author}')
    try:
        await update_bot_status()
        logger.info("Sending initial response...")
        await ctx.send("🔥 Generating savage NWA roast...")

        logger.info("Generating roast text...")
        roast_text = await generate_roast()

        logger.info(f"Sending roast: {roast_text}")
        await ctx.send(roast_text)
        logger.info("Successfully sent roast")
    except Exception as e:
        logger.error(f"Error in roast command: {str(e)}")
        logger.exception("Full traceback:")
        await ctx.send("Failed to roast! But LUX is still going to zero! 💀")

@bot.command(name='meme')
@commands.cooldown(1, 5, commands.BucketType.user)  # Rate limit: 1 use per 5 seconds per user
async def meme(ctx, timeframe: str = "1hr"):
    """Generate price chart meme with specified timeframe"""
    logger.info(f'Executing meme command for {ctx.author} with timeframe {timeframe}')
    try:
        await update_bot_status()

        # Validate timeframe
        valid_timeframes = {"5m", "15m", "1hr"}
        if timeframe not in valid_timeframes:
            logger.warning(f"Invalid timeframe requested: {timeframe}")
            await ctx.send("❌ Invalid timeframe! Use 5m, 15m, or 1hr")
            return

        logger.info(f"Starting meme generation with timeframe {timeframe}")
        message = await ctx.send(f"🔥 Generating LUX price chart ({timeframe})... 📉")

        logger.info("Calling generate_meme function...")
        meme_path = await generate_meme(timeframe)
        logger.info(f"Generated meme path: {meme_path}")

        if meme_path and os.path.exists(meme_path) and meme_path.endswith('.png'):
            file_size = os.path.getsize(meme_path)
            logger.info(f"Sending meme file: {meme_path} (size: {file_size} bytes)")

            try:
                with open(meme_path, 'rb') as f:
                    await ctx.send(file=discord.File(f))
                logger.info("Successfully sent meme file")
            except Exception as e:
                logger.error(f"Error sending meme file: {str(e)}")
                await message.edit(content="Failed to send meme! Error occurred while sending file.")
                return

            # Clean up the file
            try:
                os.remove(meme_path)
                logger.info(f"Successfully cleaned up meme file: {meme_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up meme file: {str(e)}")
        else:
            error_msg = f"Invalid meme path or file: {meme_path}"
            logger.error(error_msg)
            await message.edit(content="Failed to generate chart! LUX price data not found! 📉")
    except Exception as e:
        logger.error(f"Error in meme command: {str(e)}")
        logger.exception("Full traceback:")
        await ctx.send(f"Failed to generate meme! Error: {str(e)[:100]}... 💀")

@bot.command(name='crash')
@commands.cooldown(1, 3, commands.BucketType.user)  # Rate limit: 1 use per 3 seconds per user
async def crash(ctx):
    """Get current crash stats from price data"""
    logger.info(f'Executing crash command for {ctx.author}')
    try:
        await update_bot_status()  # Set online immediately
        await ctx.send("💥 Fetching latest LUX crash data...")
        dates, prices, _ = await get_lux_price_history()  # Ignore candles
        if dates and prices:
            current_price = prices[-1]
            crash_percent = ((0.015 - current_price) / 0.015) * 100
            price_str = format_price_label(current_price)

            crash_message = (
                f"💥 LUX CRASH UPDATE 💥\n"
                f"Current Price: {price_str}\n"
                f"Down {crash_percent:.1f}% since NWA entry! Complete rugpull! 💀"
            )

            await ctx.send(crash_message)
            logger.info(f"Sent crash stats: {crash_percent:.1f}% down, price: {price_str}")
        else:
            await ctx.send("💥 LUX CRASH UPDATE 💥\nPrice too low to calculate! Complete rugpull! 💀")
            logger.warning("Using fallback crash message due to missing price data")
    except Exception as e:
        logger.error(f"Error in crash command: {str(e)}")
        logger.exception("Full traceback:")
        await ctx.send("💥 LUX CRASH UPDATE 💥\nDown 99.9%! Complete rugpull! 💀")

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    logger.info(f'Executing help command for {ctx.author}')
    await update_bot_status()  # Set online immediately
    help_text = """
🔥 **$LUXSUX Bot Commands** 🔥
• `!roast` - Get a savage roast about LUX
• `!meme [timeframe]` - Generate a price chart meme
  - Timeframes: 5m, 15m, 1hr
• `!crash` - See how much LUX crashed
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    restart_delay = 5
    max_retries = float('inf')  # Infinite retries
    retry_count = 0
    last_restart = datetime.now()

    while retry_count < max_retries:
        try:
            logger.info("Starting bot...")
            # Enhanced connection settings
            bot.run(
                TOKEN,
                reconnect=True,
                log_handler=None,  # Prevent duplicate logging
                log_formatter=None
            )
        except Exception as e:
            retry_count += 1
            current_time = datetime.now()
            # Reset retry count if last restart was more than 1 hour ago
            if current_time - last_restart > timedelta(hours=1):
                retry_count = 0
                restart_delay = 5

            logger.error(f"Bot crashed (attempt {retry_count}): {str(e)}")
            logger.error(f"Restarting in {restart_delay} seconds...")
            logger.exception("Full traceback:")
            time.sleep(restart_delay)
            # Increase delay for next retry, max 30 seconds
            restart_delay = min(restart_delay * 1.5, 30)
            last_restart = current_time
            continue

def format_price_label(price):
    """Formats the price for display,  assuming this function exists elsewhere"""
    price_in_cents = price * 100
    return f"{price_in_cents:.2f}¢"