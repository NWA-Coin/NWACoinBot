import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys
from datetime import datetime
import asyncio
import signal
from keep_alive import keep_alive
from roast_generator import generate_roast
from meme_generator import generate_meme
from price_chart import get_lux_price_history, format_price_label
from market_data import get_solana_token_by_contract
from supervisor import BotSupervisor
from wallet_manager import WalletManager

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
    sys.exit(1)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    reconnect=True,
    case_insensitive=True
)

# Remove default help command
bot.remove_command('help')

wallet_manager = None

@bot.event
async def on_ready():
    """Called when the bot successfully connects"""
    global wallet_manager
    try:
        logger.info("Initializing wallet manager...")
        wallet_manager = WalletManager()
        logger.info("Wallet manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize wallet manager: {str(e)}")
        logger.exception("Full traceback:")
        return

    logger.info(f'Logged in as {bot.user.name} ($LUXSUX)')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info('Bot is ready!')

    await bot.change_presence(
        activity=discord.Game(name="!help | Roasting Crypto"),
        status=discord.Status.online
    )

@bot.event
async def on_resumed():
    """Log when the bot resumes a session after disconnect"""
    logger.info("Bot resumed connection")
    await bot.change_presence(
        activity=discord.Game(name="!help | Roasting Crypto"),
        status=discord.Status.online
    )

@bot.event
async def on_disconnect():
    """Log disconnection"""
    logger.warning("Bot disconnected. Attempting to reconnect...")

@bot.event
async def on_message(message):
    """Handle incoming messages with improved error handling"""
    if message.author == bot.user:
        return

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
async def on_command(ctx):
    """Log when commands are used"""
    logger.info(f'Command "{ctx.command}" used by {ctx.author} in {ctx.guild}')

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    logger.error(f"Command error occurred: {str(error)}")
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Command on cooldown. Try again in {error.retry_after:.1f}s")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use !help to see available commands.")
    else:
        logger.error(f'Error in command "{ctx.command}": {str(error)}')
        await ctx.send("❌ Command failed! Try !help to see available commands.")

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle any uncaught exceptions"""
    logger.error(f'Error in {event}:')
    logger.exception('Traceback:')

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
        await bot.change_presence(
            activity=discord.Game(name="!help | Roasting Crypto"),
            status=discord.Status.online
        )
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
async def meme(ctx, token: str = "$lux", timeframe: str = "7d"):
    """Generate price chart meme with specified token and timeframe"""
    logger.info(f'Starting meme command execution for {ctx.author} with token {token} and timeframe {timeframe}')
    try:
        await bot.change_presence(
            activity=discord.Game(name="!help | Roasting Crypto"),
            status=discord.Status.online
        )

        # Clean token input
        token = token.strip('$').lower()

        # Handle LUX separately as it's our primary token
        if token == "lux":
            token_id = "lux-token"
            token_name = "LUX"
            token_symbol = "LUX"
            entry_price = 0.015  # NWA entry price
        else:
            # Validate contract address format (simple check)
            if not (len(token) == 43 or len(token) == 44):  # Solana addresses are typically 43/44 chars
                await ctx.send("❌ Invalid Solana contract address! Please provide a valid Solana contract address.")
                return

            # Show searching message
            message = await ctx.send(f"🔍 Searching for token info for contract: {token}...")

            # Get token info using contract address
            token_info = await get_solana_token_by_contract(token)
            if not token_info:
                await message.edit(content=f"❌ No token found for contract address: {token}")
                return

            token_id, token_name, token_symbol = token_info
            entry_price = None  # No entry price for other tokens

            # Update message with found token info
            await message.edit(content=f"📊 Generating chart for {token_name} ({token_symbol})...")

        # Validate timeframe
        valid_timeframes = {"1hr", "24hr", "7d", "1m", "3m"}
        if timeframe not in valid_timeframes:
            logger.warning(f"Invalid timeframe requested: {timeframe}")
            await ctx.send("❌ Invalid timeframe! Use 1hr, 24hr, 7d, 1m, or 3m")
            return

        # Generate meme
        logger.info("Starting meme generation process")
        meme_path = await generate_meme(
            timeframe=timeframe,
            token_id=token_id,
            token_symbol=token_symbol,
            entry_price=entry_price
        )

        if meme_path and os.path.exists(meme_path):
            try:
                # Send the meme file
                logger.info("Sending meme file to Discord")
                with open(meme_path, 'rb') as f:
                    await ctx.send(file=discord.File(f))
                if 'message' in locals():
                    await message.delete()
                logger.info("Successfully sent meme and cleaned up message")
            except Exception as e:
                logger.error(f"Error sending meme file: {str(e)}")
                if 'message' in locals():
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
            if 'message' in locals():
                await message.edit(content=f"Failed to generate chart! Token data not found! 📉")
            else:
                await ctx.send(f"Failed to generate chart! Token data not found! 📉")
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
        await bot.change_presence(
            activity=discord.Game(name="!help | Roasting Crypto"),
            status=discord.Status.online
        )
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


@bot.command(name='linkwallet')
@commands.cooldown(1, 30, commands.BucketType.user)  # Rate limit: 1 use per 30 seconds per user
async def link_wallet(ctx, wallet_address: str = None):
    """Link your NWA wallet to your Discord account"""
    if not wallet_manager:
        await ctx.send("❌ Wallet system is currently unavailable")
        return

    if not wallet_address:
        await ctx.send("❌ Please provide your Solana wallet address!\nUsage: !linkwallet <address>")
        return

    try:
        success, result = await wallet_manager.link_wallet(ctx.author.id, wallet_address)

        if success:
            # Result contains verification code
            message = (
                f"🔗 Linking NWA wallet `{wallet_address}`\n\n"
                f"To verify ownership, send `0` SOL to this same wallet with this memo:\n"
                f"`{result}`\n\n"
                f"Then use `!verifywallet {result}` to complete verification"
            )
            # Send verification instructions in DM for privacy
            try:
                await ctx.author.send(message)
                await ctx.send("📬 Check your DMs for verification instructions!")
            except discord.Forbidden:
                await ctx.send("❌ I couldn't DM you! Please enable DMs from server members.")
        else:
            await ctx.send(f"❌ {result}")
    except Exception as e:
        logger.error(f"Error in link_wallet command: {str(e)}")
        await ctx.send("❌ Failed to process wallet linking")

@bot.command(name='verifywallet')
@commands.cooldown(1, 30, commands.BucketType.user)  # Rate limit: 1 use per 30 seconds per user
async def verify_wallet(ctx, verification_code: str = None):
    """Verify your NWA wallet ownership using the verification code"""
    if not wallet_manager:
        await ctx.send("❌ Wallet system is currently unavailable")
        return

    if not verification_code:
        await ctx.send("❌ Please provide the verification code!\nUsage: !verifywallet <code>")
        return

    try:
        success, message = await wallet_manager.verify_wallet(ctx.author.id, verification_code)
        if success:
            await ctx.send(f"✅ {message}")
        else:
            await ctx.send(f"❌ {message}")
    except Exception as e:
        logger.error(f"Error in verify_wallet command: {str(e)}")
        await ctx.send("❌ Failed to verify wallet")

@bot.command(name='wallet')
@commands.cooldown(1, 5, commands.BucketType.user)  # Rate limit: 1 use per 5 seconds per user
async def list_wallet(ctx):
    """Show your linked NWA wallet"""
    if not wallet_manager:
        await ctx.send("❌ Wallet system is currently unavailable")
        return

    try:
        wallet = await wallet_manager.get_user_wallet(ctx.author.id)

        if not wallet:
            await ctx.send("🏦 You don't have a verified NWA wallet linked. Use !linkwallet to link one!")
            return

        # Create a formatted wallet display
        status = "✅ Airdrop Claimed" if wallet['airdrop_claimed'] else "⏳ Airdrop Pending"
        wallet_info = (
            f"🏦 Your NWA Wallet:\n"
            f"Address: `{wallet['wallet_address']}`\n"
            f"Linked: <t:{int(wallet['created_at'].timestamp())}:R>\n"
            f"Status: {status}"
        )

        await ctx.send(wallet_info)
    except Exception as e:
        logger.error(f"Error in list_wallet command: {str(e)}")
        await ctx.send("❌ Failed to retrieve wallet info")

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    logger.info(f'Executing help command for {ctx.author}')
    await bot.change_presence(
        activity=discord.Game(name="!help | NWA Token"),
        status=discord.Status.online
    )
    help_text = """
🔥 **NWA Bot Commands** 🔥
• `!ping` - Check if bot is active
• `!roast` - Get a savage roast about LUX
• `!meme [token] [timeframe]` - Generate a price chart meme
  - Use $LUX or paste a Solana contract address
  - Timeframes: 1hr, 24hr, 7d, 1m, 3m
• `!crash` - See how much LUX crashed

🏦 **NWA Wallet Commands** 🏦
• `!linkwallet <address>` - Link your NWA wallet
• `!verifywallet <code>` - Verify wallet ownership
• `!wallet` - Show your NWA wallet info
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
    try:
        if not bot.is_closed():
            logger.info("Closing bot connection...")
            asyncio.create_task(bot.close())
        logger.info("Cleanup complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

async def shutdown(bot):
    """Async shutdown handler"""
    try:
        if not bot.is_closed():
            await bot.close()
            logger.info("Bot connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


async def main():
    """Main async entry point with enhanced error handling"""
    try:
        # Start keep-alive server
        logger.info("Starting keep-alive server...")
        keep_alive_port = keep_alive()
        if not keep_alive_port:
            logger.error("Failed to start keep-alive server")
            return

        logger.info(f"Keep-alive server started on port {keep_alive_port}")

        # Initialize supervisor with keep-alive port
        supervisor = BotSupervisor(keep_alive_port)
        supervisor.setup_signal_handlers()

        # Start the bot with proper error handling
        async with bot:
            logger.info("Starting bot supervisor monitoring...")
            monitor_task = bot.loop.create_task(supervisor.monitor(bot))

            logger.info("Starting bot with Discord token...")
            try:
                await bot.start(TOKEN)
            except Exception as e:
                logger.error(f"Failed to start bot: {str(e)}")
                monitor_task.cancel()
                raise

    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}")
        logger.exception("Full traceback:")
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        logger.info("Starting bot main sequence...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.critical(f"Failed to start bot: {str(e)}")
        logger.exception("Full traceback:")
    finally:
        logger.info("Bot shutdown complete")