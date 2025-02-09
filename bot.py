import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup with minimal required intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

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
    print(f'{bot.user} has connected to Discord!')
    print('Bot is ready to roast!')

    # Generate invite link
    permissions = discord.Permissions()
    permissions.send_messages = True
    permissions.read_messages = True

    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=permissions
    )
    print(f'\nInvite link for the bot:\n{invite_link}')

@bot.command(name='roast')
async def roast_lux(ctx):
    """Send a random roast about Lux coin."""
    try:
        roast = random.choice(ROASTS)
        await ctx.send(f"🔥 {roast}")
    except Exception as e:
        print(f"Error in roast command: {str(e)}")
        await ctx.send("Oops! Something went wrong. Please try again later! 😢")

@bot.command(name='commands')
async def show_commands(ctx):
    """Show available commands."""
    help_text = """
**Available Commands:**
`!roast` - Get a random roast about Lux coin
`!commands` - Show this command list
    """
    await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        raise ValueError("No Discord token found in environment variables!")
    bot.run(token)