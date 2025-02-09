import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
from roast_generator import generate_roast, create_meme_image

# Load environment variables
load_dotenv()

# Bot setup with absolute minimum intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Store custom roasts in memory
CUSTOM_ROASTS = set()

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
        permissions.attach_files = True  # Add permission to attach files for memes

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
        # Combine built-in and custom roasts
        all_roasts = list(CUSTOM_ROASTS) + [generate_roast()]
        roast = random.choice(all_roasts)
        await ctx.send(f"🔥 {roast}")
    except Exception as e:
        print(f"Error in roast command: {str(e)}")
        await ctx.send("❌ Oops! Something went wrong. Please try again later!")

@bot.command(name='memeroast')
async def meme_roast_lux(ctx):
    """Send a random roast about Lux coin as a meme image."""
    try:
        # Combine built-in and custom roasts
        all_roasts = list(CUSTOM_ROASTS) + [generate_roast()]
        roast = random.choice(all_roasts)

        # Generate meme image
        meme_bytes = create_meme_image(roast)

        # Send the meme
        await ctx.send(
            file=discord.File(fp=meme_bytes, filename='lux_roast.png'),
            content=f"🔥 Generated a spicy meme roast for you!"
        )
    except Exception as e:
        print(f"Error in memeroast command: {str(e)}")
        await ctx.send("❌ Failed to generate meme roast. Please try again!")

@bot.command(name='addroast')
async def add_custom_roast(ctx, *, roast_text: str):
    """Add a custom roast to the collection."""
    try:
        if not roast_text:
            await ctx.send("❌ Please provide the roast text! Usage: `!addroast <your roast here>`")
            return

        # Add the roast to custom collection
        CUSTOM_ROASTS.add(roast_text)
        await ctx.send(f"✅ Added your custom roast!\n🔥 Preview: {roast_text}")
    except Exception as e:
        print(f"Error in addroast command: {str(e)}")
        await ctx.send("❌ Failed to add roast. Please try again!")

@bot.command(name='listroasts')
async def list_custom_roasts(ctx):
    """List all custom roasts with their index numbers."""
    try:
        if not CUSTOM_ROASTS:
            await ctx.send("📝 No custom roasts added yet! Use `!addroast` to add some.")
            return

        roast_list = "📝 **Custom Roasts:**\n"
        for idx, roast in enumerate(CUSTOM_ROASTS, 1):
            roast_list += f"{idx}. {roast}\n"

        await ctx.send(roast_list)
    except Exception as e:
        print(f"Error in listroasts command: {str(e)}")
        await ctx.send("❌ Failed to list roasts. Please try again!")

@bot.command(name='deleteroast')
async def delete_custom_roast(ctx, index: int):
    """Delete a custom roast by its index number."""
    try:
        if not CUSTOM_ROASTS:
            await ctx.send("📝 No custom roasts to delete!")
            return

        if index < 1 or index > len(CUSTOM_ROASTS):
            await ctx.send(f"❌ Invalid index! Use `!listroasts` to see available roasts and their numbers (1-{len(CUSTOM_ROASTS)}).")
            return

        # Convert set to list to access by index
        roast_list = list(CUSTOM_ROASTS)
        deleted_roast = roast_list[index - 1]
        CUSTOM_ROASTS.remove(deleted_roast)

        await ctx.send(f"✅ Deleted roast: {deleted_roast}")
    except ValueError:
        await ctx.send("❌ Please provide a valid number! Usage: `!deleteroast <number>`")
    except Exception as e:
        print(f"Error in deleteroast command: {str(e)}")
        await ctx.send("❌ Failed to delete roast. Please try again!")

@bot.command(name='commands')
async def show_commands(ctx):
    """Show available commands."""
    try:
        help_text = """**Available Commands:**
`!roast` - Get a random roast about Lux coin
`!memeroast` - Get a random roast as a meme image
`!addroast <text>` - Add your own custom roast
`!listroasts` - Show all custom roasts with their numbers
`!deleteroast <number>` - Delete a custom roast by its number"""
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