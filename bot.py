import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys
import time
from datetime import datetime, timedelta
import asyncio
import signal
import atexit
import requests
from keep_alive import keep_alive
from roast_generator import generate_roast
from meme_generator import generate_meme
from price_chart import get_lux_price_history, format_price_label
from supervisor import BotSupervisor

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
    max_messages=10000,
    chunk_guilds_at_startup=False,
    heartbeat_timeout=150.0
)

# Remove default help command
bot.remove_command('help')

# Constants for health monitoring
HEALTH_CHECK_INTERVAL = 30  # seconds
HEALTH_CHECK_PORTS = [8080, 8000, 5000]  # Possible keep-alive server ports
MAX_STARTUP_RETRIES = 5
STARTUP_RETRY_DELAY = 5  # seconds

async def wait_for_keep_alive_server():
    """Wait for keep-alive server to be ready"""
    logger.info("Waiting for keep-alive server to start...")
    retries = 0

    while retries < MAX_STARTUP_RETRIES:
        for port in HEALTH_CHECK_PORTS:
            try:
                # Try to connect to keep-alive server
                response = requests.get(f"http://localhost:{port}/")
                if response.status_code == 200 and response.text == "Bot is alive!":
                    logger.info(f"Keep-alive server found on port {port}")
                    return True
            except requests.RequestException:
                pass

        retries += 1
        if retries < MAX_STARTUP_RETRIES:
            logger.warning(f"Keep-alive server not ready, retry {retries}/{MAX_STARTUP_RETRIES}")
            await asyncio.sleep(STARTUP_RETRY_DELAY)

    logger.error("Failed to connect to keep-alive server")
    return False

async def initialize_bot():
    """Initialize bot with proper startup sequence"""
    try:
        # Start the keep-alive server
        if not keep_alive():
            logger.error("Failed to start keep-alive server")
            return False

        # Wait for keep-alive server to be ready
        if not await wait_for_keep_alive_server():
            logger.error("Keep-alive server failed to start")
            return False

        # Start supervisor monitoring
        supervisor = BotSupervisor()
        supervisor.setup_signal_handlers()
        bot.loop.create_task(supervisor.monitor(bot))

        return True
    except Exception as e:
        logger.error(f"Error during bot initialization: {str(e)}")
        return False

async def on_ready():
    """Called when the bot successfully connects/reconnects"""
    global reconnect_attempts, last_heartbeat
    reconnect_attempts = 0  # Reset counter on successful connection
    last_heartbeat = datetime.now()

    logger.info(f'Logged in as {bot.user.name} ($LUXSUX)')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info('Bot is ready!')
    logger.info('Available commands: !help, !roast, !meme, !crash, !ping')

    # Start supervisor monitoring
    bot.loop.create_task(supervisor.monitor(bot))
    logger.info("Started bot supervisor monitoring")

async def monitor_heartbeat():
    """Monitor bot's heartbeat and force reconnect if needed"""
    global last_heartbeat, reconnect_attempts
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            if datetime.now() - last_heartbeat > timedelta(seconds=HEARTBEAT_TIMEOUT):
                logger.warning(f"No heartbeat detected for {HEARTBEAT_TIMEOUT} seconds")
                await handle_disconnection()
        except Exception as e:
            logger.error(f"Error in heartbeat monitor: {str(e)}")
            await asyncio.sleep(5)

async def handle_disconnection():
    """Handle bot disconnection with exponential backoff"""
    global reconnect_attempts
    try:
        reconnect_attempts += 1
        delay = min(RECONNECT_BASE_DELAY * (2 ** (reconnect_attempts - 1)), MAX_RECONNECT_DELAY)
        logger.info(f"Attempting reconnection (attempt {reconnect_attempts}) after {delay}s delay")

        if not bot.is_closed():
            await bot.close()  # Clean disconnect if needed

        await asyncio.sleep(delay)

        if bot.is_closed():
            # Force restart the entire bot if needed
            await bot.start(TOKEN, reconnect=True)
            logger.info("Bot successfully reconnected")
            await update_bot_status()
    except Exception as e:
        logger.error(f"Reconnection attempt failed: {str(e)}")
        await asyncio.sleep(5)

@bot.event
async def on_resumed():
    """Log when the bot resumes a session after disconnect"""
    logger.info("Bot resumed connection")
    await update_bot_status()

@bot.event
async def on_disconnect():
    """Log disconnection and attempt immediate reconnect"""
    logger.warning("Bot disconnected. Attempting to reconnect...")
    await asyncio.sleep(1)  # Brief delay before next attempt

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle any uncaught exceptions"""
    logger.error(f'Error in {event}:')
    logger.exception('Traceback:')

@bot.event
async def on_message(message):
    """Handle incoming messages with improved error handling"""
    if message.author == bot.user:
        return

    # Add more detailed logging
    logger.info(f"Received message: {message.content[:50]}... from {message.author}")

    # Only process messages from guilds (servers), not DMs
    if not message.guild:
        logger.info("Ignoring DM message")
        return

    # Process commands with enhanced error handling
    if message.content.startswith(bot.command_prefix):
        logger.info(f"Processing command: {message.content} from {message.author}")
        try:
            await bot.process_commands(message)
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
            logger.exception("Full command processing traceback:")
            await message.channel.send("❌ Error processing command. Please try again.")

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

# Add enhanced logging to ping command for better visibility
@bot.command(name='ping')
@commands.cooldown(1, 2, commands.BucketType.user)  # Rate limit: 1 use per 2 seconds per user
async def ping(ctx):
    """Check bot status and latency"""
    logger.info(f'Executing ping command for {ctx.author}')
    try:
        # Calculate round-trip latency
        latency = round(bot.latency * 1000)  # Convert to milliseconds

        # Send response with latency and status
        status_msg = f"🏓 Pong! Bot is active and healthy! (`{latency}ms`)\n"
        status_msg += "✅ All systems operational"

        await ctx.send(status_msg)
        logger.info(f"Ping response sent with latency: {latency}ms")
    except Exception as e:
        logger.error(f"Error in ping command: {str(e)}")
        await ctx.send("❌ Error checking status!")

@bot.command(name='roast')
@commands.cooldown(1, 3, commands.BucketType.user)  # Rate limit: 1 use per 3 seconds per user
async def roast(ctx):
    """Generate a savage roast"""
    logger.info(f'Executing roast command for {ctx.author}')
    try:
        await update_bot_status()
        logger.info("Sending initial response...")
        message = await ctx.send("🔥 Generating savage NWA roast...")

        logger.info("Generating roast text...")
        roast_text = await generate_roast()

        logger.info(f"Sending roast: {roast_text}")
        await message.edit(content=roast_text)
        logger.info("Successfully sent roast")
    except Exception as e:
        logger.error(f"Error in roast command: {str(e)}")
        logger.exception("Full traceback:")
        await ctx.send("Failed to roast! But LUX is still going to zero! 💀")

@bot.command(name='meme')
@commands.cooldown(1, 5, commands.BucketType.user)  # Rate limit: 1 use per 5 seconds per user
async def meme(ctx, timeframe: str = "1hr"):
    """Generate price chart meme with specified timeframe"""
    logger.info(f'Starting meme command execution for {ctx.author} with timeframe {timeframe}')
    try:
        await update_bot_status()

        # Validate timeframe
        valid_timeframes = {"5m", "15m", "1hr"}
        if timeframe not in valid_timeframes:
            logger.warning(f"Invalid timeframe requested: {timeframe}")
            await ctx.send("❌ Invalid timeframe! Use 5m, 15m, or 1hr")
            return

        # Send initial message
        logger.info(f"Sending initial message for timeframe {timeframe}")
        message = await ctx.send(f"🔥 Generating LUX price chart ({timeframe})... 📉")

        # Generate meme
        logger.info("Starting meme generation process")
        meme_path = await generate_meme(timeframe)
        logger.info(f"Meme generation completed, path: {meme_path}")

        if meme_path and os.path.exists(meme_path):
            try:
                # Send the meme file
                logger.info("Sending meme file to Discord")
                with open(meme_path, 'rb') as f:
                    await ctx.send(file=discord.File(f))
                await message.delete()
                logger.info("Successfully sent meme and cleaned up message")
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
        await update_bot_status()
        message = await ctx.send("💥 Fetching latest LUX crash data...")

        logger.info("Attempting to fetch price history")
        timestamps, prices = await get_lux_price_history()

        if timestamps and prices:
            current_price = prices[-1]
            crash_percent = ((0.015 - current_price) / 0.015) * 100
            price_str = format_price_label(current_price)

            logger.info(f"Successfully fetched price data - Current: {price_str}, Down: {crash_percent:.1f}%")

            crash_message = (
                f"💥 LUX CRASH UPDATE 💥\n"
                f"Current Price: {price_str}\n"
                f"Down {crash_percent:.1f}%! Complete rugpull! 💀"
            )

            await message.edit(content=crash_message)
            logger.info(f"Sent crash stats: {crash_percent:.1f}% down, price: {price_str}")
        else:
            logger.error("Failed to fetch price data - no valid data returned")
            await message.edit(content="💥 LUX CRASH UPDATE 💥\nPrice too low to calculate! Complete rugpull! 💀")
    except Exception as e:
        logger.error(f"Error in crash command: {str(e)}")
        logger.exception("Full traceback:")
        await ctx.send("💥 LUX CRASH UPDATE 💥\nDown 99.9%! Complete rugpull! 💀")

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    logger.info(f'Executing help command for {ctx.author}')
    await update_bot_status()
    help_text = """
🔥 **$LUXSUX Bot Commands** 🔥
• `!ping` - Check if bot is active
• `!roast` - Get a savage roast about LUX
• `!meme [timeframe]` - Generate a price chart meme
  - Timeframes: 5m, 15m, 1hr
• `!crash` - See how much LUX crashed
    """
    await ctx.send(help_text)

def format_price_label(price):
    """Format price in cents"""
    price_in_cents = price * 100
    return f"{price_in_cents:.2f}¢"

# Enhanced shutdown handling
def cleanup():
    """Cleanup function to handle graceful shutdown"""
    logger.info("Bot cleanup initiated")
    if not bot.is_closed():
        logger.info("Closing bot connection...")
        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
    logger.info("Cleanup complete")

atexit.register(cleanup)

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    try:
        logger.info("Starting bot initialization sequence...")

        # Run initialization in event loop
        loop = asyncio.get_event_loop()
        if not loop.run_until_complete(initialize_bot()):
            logger.critical("Bot initialization failed")
            sys.exit(1)

        logger.info("Starting bot with enhanced supervision...")
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Critical bot error: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)  # Let the process manager handle restart

# Constants for reconnection handling
KEEP_ALIVE_INTERVAL = 30  # Increased to reduce unnecessary checks
HEARTBEAT_TIMEOUT = 120   # 2 minutes timeout
RECONNECT_BASE_DELAY = 5  # Base delay for exponential backoff
last_heartbeat = datetime.now()
reconnect_attempts = 0
MAX_RECONNECT_DELAY = 30  # Maximum seconds between reconnect attempts
bot.loop.create_task(monitor_heartbeat())