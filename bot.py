import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys
from meme_generator import generate_meme

# Set up logging with more detailed format from original code, but using basic level from edited code
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
    logger.error("No Discord token found!")
    exit(1)

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Remove default help command
bot.remove_command('help')

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info('Bot is ready!')
    logger.info('Available commands: !help, !roast, !meme, !crash')

@bot.event
async def on_command(ctx):
    """Log when commands are used"""
    logger.info(f'Command "{ctx.command.name}" used by {ctx.author} in {ctx.guild}')

@bot.event
async def on_command_error(ctx, error):
    """Log command errors"""
    logger.error(f'Error in command "{ctx.command}": {str(error)}')
    await ctx.send("❌ Command failed! Try !help to see available commands.")

@bot.command(name='roast')
async def roast(ctx):
    """Generate a savage roast"""
    logger.info(f'Executing roast command for {ctx.author}')
    try:
        await ctx.send("🔥 Generating savage NWA roast...")
        roast_text = generate_roast()
        await ctx.send(roast_text)
        logger.info("Successfully sent roast")
    except Exception as e:
        logger.error(f"Error in roast command: {str(e)}")
        await ctx.send("Failed to roast! But LUX is still going to zero! 💀")

@bot.command(name='meme')
async def meme(ctx):
    """Generate price chart meme"""
    logger.info(f'Executing meme command for {ctx.author}')
    try:
        await ctx.send("🔥 Generating LUX price chart... 📉")
        meme_path = generate_meme()

        if meme_path and meme_path.endswith('.png'):
            # Send the generated chart
            with open(meme_path, 'rb') as f:
                await ctx.send(file=discord.File(f))
            # Clean up the file
            os.remove(meme_path)
            logger.info("Successfully sent price chart meme")
        else:
            # Handle case where image generation failed
            await ctx.send(meme_path or "Failed to generate chart! Probably rugpulled to zero! 💀")
    except Exception as e:
        logger.error(f"Error in meme command: {str(e)}")
        await ctx.send("Failed to generate meme! Chart's probably dead like LUX's future! 💀")

@bot.command(name='crash')
async def crash(ctx):
    """Basic crash stats"""
    logger.info(f'Executing crash command for {ctx.author}')
    await ctx.send("💥 LUX CRASH UPDATE 💥\nDown 99.9%! Complete rugpull! 💀")

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    logger.info(f'Executing help command for {ctx.author}')
    help_text = """
🔥 **LUX Roast Bot Commands** 🔥
• `!roast` - Get a savage roast about LUX
• `!meme` - Generate a price chart meme
• `!crash` - See how much LUX crashed
    """
    await ctx.send(help_text)

if __name__ == "__main__":
    logger.info("Starting bot...")
    bot.run(TOKEN)