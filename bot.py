import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from price_chart import generate_price_chart
from roast_generator import generate_roast
import asyncio

# Load environment variables
load_dotenv()

# Bot setup with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Command cooldowns to prevent duplicate execution
command_cooldowns = {}

def commands_ready():
    """Check if commands are ready to be used again."""
    current_time = asyncio.get_event_loop().time()
    for cmd, timestamp in list(command_cooldowns.items()):
        if current_time - timestamp > 3:  # 3 second cooldown
            del command_cooldowns[cmd]

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    print(f'Logged in as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print('Bot is ready!')

    # Print invite link
    print('\nInvite link:')
    print(f'https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=2048&scope=bot%20applications.commands')

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found! Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ I don't have permission to do that!")
    else:
        print(f"Error: {str(error)}")
        await ctx.send("❌ An error occurred. Please try again!")

@bot.command(name='lux')
async def lux_price(ctx):
    """Show current LUX token price."""
    cmd_key = f"lux_{ctx.channel.id}"
    current_time = asyncio.get_event_loop().time()

    if cmd_key in command_cooldowns:
        return  # Ignore if command is on cooldown

    command_cooldowns[cmd_key] = current_time
    print(f"Processing !lux command from {ctx.author}")

    try:
        async with ctx.typing():
            chart = generate_price_chart()
            if chart:
                await ctx.send(
                    "💰 Current LUX/USD Price:",
                    file=discord.File(fp=chart, filename='lux_price.png')
                )
            else:
                await ctx.send("❌ Failed to fetch price data. Please try again!")
    except Exception as e:
        print(f"Error in lux command: {str(e)}")
        await ctx.send("❌ Something went wrong. Please try again!")

@bot.command(name='roast')
async def roast_command(ctx):
    """Generate a roast about Lux coin."""
    cmd_key = f"roast_{ctx.channel.id}"
    current_time = asyncio.get_event_loop().time()

    if cmd_key in command_cooldowns:
        return  # Ignore if command is on cooldown

    command_cooldowns[cmd_key] = current_time
    print(f"Processing !roast command from {ctx.author}")

    try:
        async with ctx.typing():
            roast = generate_roast()
            await ctx.send(roast)
    except Exception as e:
        print(f"Error in roast command: {str(e)}")
        await ctx.send("❌ Failed to generate roast. Please try again!")

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands."""
    cmd_key = f"help_{ctx.channel.id}"
    current_time = asyncio.get_event_loop().time()

    if cmd_key in command_cooldowns:
        return  # Ignore if command is on cooldown

    command_cooldowns[cmd_key] = current_time

    help_text = """
**Available Commands:**
`!lux` - Show current LUX token price
`!roast` - Get a witty roast about Lux coin
`!help` - Show this help message
"""
    await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: No Discord token found!")
        exit(1)
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("Error: Failed to login. Invalid token!")
    except Exception as e:
        print(f"Error: Failed to start bot: {str(e)}")