import os
import discord
from discord.ext import commands
import json
from openai_integration import generate_roast, generate_meme_image, add_text_to_image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup with all privileged intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable members intent
intents.presences = True  # Enable presence intent
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('Ready to roast some Lux!')

@bot.command(name='roast')
async def roast_lux(ctx):
    """Generate and send a meme roasting Lux coin."""
    try:
        # Send initial message
        await ctx.send("Generating a spicy meme about Lux... 🔥")

        # Generate roast text
        roast_response = generate_roast()
        roast_data = json.loads(roast_response)
        roast_text = roast_data['roast']

        # Generate meme image
        image_url = generate_meme_image(roast_text)

        # Add text to image
        meme_image = add_text_to_image(image_url, roast_text)

        # Send the meme
        await ctx.send(
            file=discord.File(meme_image, filename='lux_roast.png')
        )

    except Exception as e:
        await ctx.send(f"Oops! Something went wrong: {str(e)}")

@bot.command(name='commands')
async def show_commands(ctx):
    """Show available commands."""
    help_text = """
**Available Commands:**
`!roast` - Generate a meme roasting Lux coin
`!commands` - Show this help message
    """
    await ctx.send(help_text)

# Run the bot
if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        raise ValueError("No Discord token found in environment variables!")
    bot.run(token)