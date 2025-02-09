import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup with absolute minimum intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Explicitly disable help command

# Predefined roast messages
ROASTS = [
    "Lux coin is so slow, even Internet Explorer feels fast! 🐌",
    "Lux's market cap is smaller than my coffee budget! ☕",
    "Lux coin has more forks than a restaurant supply store! 🍴",
    "Lux's roadmap is like my GPS - always 'recalculating'! 🗺️",
    "Lux coin is so volatile, roller coasters look stable! 🎢",
    "Lux's white paper has more plot twists than a soap opera! 📺",
    "Investing in Lux is like trying to catch falling knives... blindfolded! 🔪",
    "Lux coin updates slower than my grandma's internet! 👵",
    "Lux's code has more bugs than a summer picnic! 🐜",
    "Lux coin makes Internet Explorer look cutting edge! 💻"
]

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    try:
        print(f'Logged in as {bot.user.name}')
        print(f'Bot ID: {bot.user.id}')
        print('Bot is ready to roast!')

        # Generate invite link with minimal permissions
        permissions = discord.Permissions()
        permissions.send_messages = True
        permissions.read_messages = True

        invite_link = discord.utils.oauth_url(
            bot.user.id,
            permissions=permissions
        )
        print(f'\nInvite link for the bot:\n{invite_link}')
    except Exception as e:
        print(f"Error in on_ready: {str(e)}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found! Use `!commands` to see available commands.")
    else:
        print(f"Command error: {str(error)}")
        await ctx.send("❌ An error occurred. Please try again later!")

@bot.command(name='roast')
async def roast_lux(ctx):
    """Send a random roast about Lux coin."""
    try:
        roast = random.choice(ROASTS)
        await ctx.send(f"🔥 {roast}")
    except Exception as e:
        print(f"Error in roast command: {str(e)}")
        await ctx.send("❌ Oops! Something went wrong. Please try again later!")

@bot.command(name='commands')
async def show_commands(ctx):
    """Show available commands."""
    try:
        help_text = """
**Available Commands:**
`!roast` - Get a random roast about Lux coin
`!commands` - Show this command list
        """
        await ctx.send(help_text)
    except Exception as e:
        print(f"Error in commands command: {str(e)}")
        await ctx.send("❌ Couldn't show commands. Please try again later!")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("No Discord token found in environment variables!")
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("Failed to login: Invalid token")
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")