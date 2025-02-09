import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import asyncio
from aiohttp import web
from price_chart import generate_price_chart
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
intents.message_content = True
intents.guild_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def start_http_server():
    """Start a simple HTTP server for health checks."""
    try:
        app = web.Application()
        async def health_check(request):
            return web.Response(text="Bot is running")
        app.router.add_get('/', health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        await site.start()
        logger.info("HTTP server started on port 5000")
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {str(e)}")

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

        # Start HTTP server for health checks
        bot.loop.create_task(start_http_server())
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

@bot.command(name='lux', help="Show current LUX token price with 24h change")
async def lux_price(ctx):
    """Show current LUX token price."""
    logger.info(f"Processing !lux command from {ctx.author}")

    try:
        async with ctx.typing():
            # Send initial message
            await ctx.send("📊 Generating price chart...")

            # Generate and send price chart
            chart_buffer = generate_price_chart()
            if chart_buffer:
                await ctx.send(
                    "💰 LUX Price Chart:",
                    file=discord.File(fp=chart_buffer, filename='lux_price.png')
                )
                chart_buffer.close()
            else:
                await ctx.send("❌ Failed to generate price chart. Please try again later!")
    except Exception as e:
        logger.error(f"Error in lux command: {str(e)}")
        await ctx.send("❌ Something went wrong. Please try again later!")

@bot.command(name='roast', help="Get a witty, AI-generated roast about Lux coin")
async def roast_command(ctx):
    """Generate a roast about Lux coin."""
    logger.info(f"Processing !roast command from {ctx.author}")

    try:
        async with ctx.typing():
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