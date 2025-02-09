import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys
from meme_generator import generate_meme
from roast_generator import generate_roast
from price_chart import get_lux_price_history

# Set up logging
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

# Bot setup
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

        if meme_path and os.path.exists(meme_path) and meme_path.endswith('.png'):
            # Log file details before sending
            file_size = os.path.getsize(meme_path)
            logger.info(f"Sending meme file: {meme_path} (size: {file_size} bytes)")

            # Send the generated chart
            with open(meme_path, 'rb') as f:
                await ctx.send(file=discord.File(f))
            # Clean up the file
            try:
                os.remove(meme_path)
                logger.info(f"Successfully cleaned up meme file: {meme_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up meme file: {str(e)}")
            logger.info("Successfully sent price chart meme")
        else:
            error_msg = f"Invalid meme path or file: {meme_path}"
            logger.error(error_msg)
            await ctx.send("Failed to generate chart! Probably rugpulled to zero! 💀")
    except Exception as e:
        logger.error(f"Error in meme command: {str(e)}")
        logger.exception("Full traceback:")
        await ctx.send("Failed to generate meme! Chart's probably dead like LUX's future! 💀")

@bot.command(name='crash')
async def crash(ctx):
    """Get current crash stats from price data"""
    logger.info(f'Executing crash command for {ctx.author}')
    try:
        # Get latest price data
        await ctx.send("💥 Fetching latest LUX crash data...")
        dates, prices = await get_lux_price_history()
        if dates and prices:
            entry_price = 0.015  # NWA entry price
            current_price = prices[-1]
            crash_percent = ((entry_price - current_price) / entry_price) * 100
            price_in_cents = current_price * 100

            crash_message = (
                f"💥 LUX CRASH UPDATE 💥\n"
                f"Current Price: {price_in_cents:.4f}¢\n"  # Prominently display cents
                f"Entry Price: 1.5¢\n"  # Added for reference
                f"Down {crash_percent:.1f}% since NWA entry! Complete rugpull! 💀"
            )

            await ctx.send(crash_message)
            logger.info(f"Sent crash stats: {crash_percent:.1f}% down, price: {price_in_cents:.4f}¢")
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