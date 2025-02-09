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

    # Generate invite link with necessary permissions
    permissions = discord.Permissions()
    permissions.send_messages = True
    permissions.attach_files = True
    permissions.read_messages = True

    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=permissions
    )
    print(f'\nInvite link for the bot:\n{invite_link}')

@bot.command(name='roast')
async def roast_lux(ctx):
    """Generate and send a meme roasting Lux coin."""
    try:
        # Send initial message
        status_message = await ctx.send("Generating a spicy meme about Lux... 🔥")

        # Generate roast text
        try:
            roast_response = generate_roast()
            print(f"Roast Response: {roast_response}")  # Debug log
            roast_data = json.loads(roast_response)
            roast_text = roast_data['roast']
            print(f"Extracted roast text: {roast_text}")  # Debug log
        except Exception as e:
            print(f"Error generating roast: {str(e)}")
            await status_message.edit(content="Failed to generate roast text. Please try again later. 😢")
            return

        # Generate meme image
        try:
            image_url = generate_meme_image(roast_text)
        except Exception as e:
            print(f"Error generating meme image: {str(e)}")
            await status_message.edit(content="Failed to generate meme image. Please try again later. 😢")
            return

        # Add text to image
        try:
            meme_image = add_text_to_image(image_url, roast_text)
        except Exception as e:
            print(f"Error adding text to image: {str(e)}")
            await status_message.edit(content="Failed to create the final meme. Please try again later. 😢")
            return

        # Send the meme and update status message
        await ctx.send(file=discord.File(meme_image, filename='lux_roast.png'))
        await status_message.delete()

    except Exception as e:
        print(f"Unexpected error in roast command: {str(e)}")
        await ctx.send(f"Oops! Something unexpected went wrong. Please try again later. 😢")

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