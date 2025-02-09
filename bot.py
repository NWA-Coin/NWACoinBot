import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from price_chart import generate_price_chart
from roast_generator import generate_roast
import asyncio
import logging
from aiohttp import web
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Load environment variables
load_dotenv()

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=commands.DefaultHelpCommand())

# Command cooldowns to prevent duplicate execution
command_cooldowns = {}

def commands_ready():
    """Check if commands are ready to be used again."""
    current_time = asyncio.get_event_loop().time()
    for cmd, timestamp in list(command_cooldowns.items()):
        if current_time - timestamp > 3:  # 3 second cooldown
            del command_cooldowns[cmd]

async def start_http_server():
    """Start a simple HTTP server for health checks."""
    app = web.Application()

    async def health_check(request):
        return web.Response(text="Bot is running")

    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    logger.info("HTTP server started on port 5000")

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f'Logged in as {bot.user.name}')
    logger.info(f'Bot ID: {bot.user.id}')
    logger.info('Bot is ready!')

    # Start HTTP server for health checks
    await start_http_server()

    # Print invite link
    logger.info('\nInvite link:')
    logger.info(f'https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=2048&scope=bot%20applications.commands')

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
    cmd_key = f"lux_{ctx.channel.id}"
    current_time = asyncio.get_event_loop().time()

    if cmd_key in command_cooldowns:
        return  # Ignore if command is on cooldown

    command_cooldowns[cmd_key] = current_time
    logger.info(f"Processing !lux command from {ctx.author}")

    try:
        async with ctx.typing():
            logger.info("Generating price chart...")
            chart = generate_price_chart()
            if chart:
                logger.info("Price chart generated successfully")
                await ctx.send(
                    "💰 Current LUX/USD Price:",
                    file=discord.File(fp=chart, filename='lux_price.png')
                )
            else:
                logger.error("Failed to generate price chart")
                await ctx.send("❌ Failed to fetch price data. Market might be down or API rate limit reached. Try again in a few minutes!")
    except Exception as e:
        logger.error(f"Error in lux command: {str(e)}")
        await ctx.send("❌ Something went wrong. Please try again later!")

@bot.command(name='roast', help="Get a witty, AI-generated roast about Lux coin")
async def roast_command(ctx):
    """Generate a roast about Lux coin."""
    cmd_key = f"roast_{ctx.channel.id}"
    current_time = asyncio.get_event_loop().time()

    if cmd_key in command_cooldowns:
        return  # Ignore if command is on cooldown

    command_cooldowns[cmd_key] = current_time
    logger.info(f"Processing !roast command from {ctx.author}")

    try:
        async with ctx.typing():
            logger.info("Generating roast...")
            roast = generate_roast()
            logger.info(f"Generated roast: {roast}")
            await ctx.send(roast)
    except Exception as e:
        logger.error(f"Error in roast command: {str(e)}")
        await ctx.send("❌ Failed to generate roast. Please try again!")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("Error: No Discord token found!")
        exit(1)
    try:
        logger.info("Starting bot...")
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Error: Failed to login. Invalid token!")
    except Exception as e:
        logger.error(f"Error: Failed to start bot: {str(e)}")