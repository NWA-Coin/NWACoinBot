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

# Track connection state
last_heartbeat = datetime.now()
reconnect_attempts = 0
MAX_RECONNECT_DELAY = 30  # Maximum seconds between reconnect attempts

@bot.event
async def on_ready():
    """Called when the bot successfully connects/reconnects"""
    global reconnect_attempts, last_heartbeat
    reconnect_attempts = 0  # Reset counter on successful connection
    last_heartbeat = datetime.now()

    logger.info(f'Logged in as {bot.user.name} ($LUXSUX)')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info('Bot is ready!')
    logger.info('Available commands: !help, !roast, !meme, !crash, !ping')

    # Start keep-alive and heartbeat monitoring tasks
    bot.loop.create_task(keep_alive())
    bot.loop.create_task(monitor_heartbeat())
    logger.info("Started keep-alive and heartbeat monitoring tasks")

async def keep_alive():
    """Enhanced keep-alive loop to maintain bot connection"""
    global last_heartbeat
    logger.info("Starting keep-alive loop")
    while True:
        try:
            if not bot.is_closed():
                last_heartbeat = datetime.now()
                logger.info("Keep-alive heartbeat: Bot is active")
                await bot.change_presence(
                    activity=discord.Game(name="!help | Roasting LUX"),
                    status=discord.Status.online
                )
                await asyncio.sleep(15)  # Check every 15 seconds
            else:
                logger.warning("Keep-alive detected closed connection")
                await handle_disconnection()
                await asyncio.sleep(5)  # Brief delay before retry
        except Exception as e:
            logger.error(f"Error in keep-alive loop: {str(e)}")
            await asyncio.sleep(5)

async def monitor_heartbeat():
    """Monitor bot's heartbeat and force reconnect if needed"""
    global last_heartbeat, reconnect_attempts
    while True:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            if datetime.now() - last_heartbeat > timedelta(minutes=2):
                logger.warning("No heartbeat detected for 2 minutes")
                await handle_disconnection()
        except Exception as e:
            logger.error(f"Error in heartbeat monitor: {str(e)}")
            await asyncio.sleep(5)

async def handle_disconnection():
    """Handle bot disconnection with exponential backoff"""
    global reconnect_attempts
    try:
        reconnect_attempts += 1
        delay = min(5 * (2 ** (reconnect_attempts - 1)), MAX_RECONNECT_DELAY)
        logger.info(f"Attempting reconnection (attempt {reconnect_attempts}) after {delay}s delay")

        if not bot.is_closed():
            await bot.close()  # Clean disconnect if needed

        await asyncio.sleep(delay)

        if bot.is_closed():
            await bot.start(TOKEN, reconnect=True)

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

    # Only process messages from guilds (servers), not DMs
    if not message.guild:
        return

    # Process commands with error handling
    if message.content.startswith(bot.command_prefix):
        logger.info(f"Processing command: {message.content} from {message.author}")
        try:
            ctx = await bot.get_context(message)
            if ctx.valid:
                await bot.invoke(ctx)
        except Exception as e:
            logger.error(f"Error processing command: {str(e)}")
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

        if meme_path and os.path.exists(meme_path):
            try:
                with open(meme_path, 'rb') as f:
                    await ctx.send(file=discord.File(f))
                logger.info("Successfully sent meme file")
                await message.delete()
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

if __name__ == "__main__":
    restart_delay = 5
    max_retries = float('inf')  # Infinite retries
    retry_count = 0
    last_restart = datetime.now()

    while retry_count < max_retries:
        try:
            logger.info("Starting bot with enhanced logging...")
            logger.info(f"Discord Token length: {len(TOKEN) if TOKEN else 0}")
            logger.info("Initializing bot connection...")
            # Enhanced connection settings
            bot.run(
                TOKEN,
                reconnect=True,
                log_handler=None,  # Prevent duplicate logging
                log_formatter=None
            )
        except discord.LoginFailure as e:
            logger.error(f"Failed to login: {str(e)}")
            logger.error("Please check if the Discord token is valid")
            break  # Exit on authentication failure
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
            restart_delay = min(restart_delay * 2, 30)
            last_restart = current_time
            continue