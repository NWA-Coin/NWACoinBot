import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
from datetime import datetime
from roast_generator import generate_roast

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
intents.message_content = True  # Required for responding to messages
intents.guild_messages = True   # Required for guild messages
intents.guilds = True          # Required for guild/server join

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    description='LUX Roast Bot - Use !help to see available commands'
)

# Predefined roasts for initial testing
ROASTS = [
    "Tino's mom got fucked harder than LUX holders! Complete rug pull! 💀🔥",
    "Tino the fraud got exposed like the scam coin he shilled! Get rekt! 🖕💩",
    "LUX is more worthless than Tino's trading advice! Pure dogshit! 🐕💩",
    "Another day of Tino being a little bitch while LUX goes to zero! 📉🤡",
    "Imagine trusting Tino with your money! LUX = pure garbage! 🗑️💸"
]

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    try:
        logger.info(f'Logged in as {bot.user.name}')
        logger.info(f'Bot ID: {bot.user.id}')
        logger.info('Bot is ready!')

        # Print invite link
        logger.info('\nInvite link:')
        logger.info(f'https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=2048&scope=bot%20applications.commands')
    except Exception as e:
        logger.error(f"Error in on_ready: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found! Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ I don't have permission to do that!")
    else:
        logger.error(f"Command error: {str(error)}")
        await ctx.send("❌ An error occurred. Please try again!")

@bot.command(name='roast', help='Get a savage roast about LUX')
async def roast_command(ctx):
    """Generate a roast about LUX."""
    try:
        roast = generate_roast()
        await ctx.send(roast)
    except Exception as e:
        logger.error(f"Error in roast command: {str(e)}")
        await ctx.send("❌ Failed to generate roast. Please try again!")

if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        bot.run(TOKEN, log_handler=None)
    except discord.LoginFailure:
        logger.error("Failed to login. Invalid token!")
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")