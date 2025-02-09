import os
import random
from openai import OpenAI
import logging
from price_chart import get_lux_price_history
import asyncio

# Set up logging
logger = logging.getLogger('discord_bot')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# List of fallback roasts
FALLBACK_ROASTS = [
    # Technical/Code Roasts
    "LUX code looking like a bootcamp dropout's first project! Complete disaster! 💩👨‍💻",
    "Can't even code a proper rugpull! NWA exposing this fraud! 🔥🤡",
    "Another day of LUX smart contracts failing! Trash coder exposed! 🗑️💀",
    "Stack Overflow won't save your shitcoin! Complete failure! ⚰️👨‍💻",
    "Error 404: Coding skills not found! NWA stays winning! 🏆💯",
    "Copy-pasting code won't save LUX! Another L for this fraud! 📝🗑️",
    "Even ChatGPT writes better code! Complete failure! 🤖⚰️",

    # Project/Price Roasts
    "LUX chart looking like your credibility - straight to zero! 📉💩",
    "NWA destroying your reputation while LUX dumps! Complete disaster! 🔥💀",
    "Even your trading bot dumped LUX! Get exposed fraud! 🤖🗑️",
    "Begging ChatGPT to pump LUX! Pathetic scammer! 🤮💸",
    "Another day, another LUX rugpull! NWA stays winning! 🏆💰",
    "Zero liquidity just like your trading skills! Complete failure! 💸📉",
    "Imagine launching a token that only goes down! Pure comedy! 😂💩",

    # Mixed Content
    "Failed code + zero liquidity = complete disaster! 💩📉",
    "Error in trading bot: exit_scam.py failed! 🤖📉",
    "NWA exposing your copy-pasted code! Another L! 🔥💻",
    "Can't debug your way out of this one! 💻🐛",
    "Pushed to main and the price crashed again! Complete failure! 💩💻",
    "From junior dev to complete failure! Stay losing! 🤡👨‍💻",
    "Commit history: 100% copypasta! Pure garbage! 💩💻"
]

async def get_crash_stats():
    """Get crash stats for roast."""
    try:
        timestamps, prices = await get_lux_price_history()  # Updated to unpack two values
        if prices:
            entry_price = 0.015  # NWA entry price
            current_price = prices[-1]
            crash_percent = ((entry_price - current_price) / entry_price) * 100
            price_in_cents = current_price * 100
            logger.info(f"Calculated crash stats: {crash_percent:.1f}% down, price: {price_in_cents:.4f}¢")
            return crash_percent, price_in_cents
        return None, None
    except Exception as e:
        logger.error(f"Error getting crash stats: {str(e)}")
        return None, None

async def generate_roast():
    """Generate a savage roast focusing on technical and project failures."""
    try:
        logger.info("Starting roast generation")

        # Get crash stats
        try:
            crash_percent, price_in_cents = await get_crash_stats()
        except Exception as e:
            logger.error(f"Error getting crash stats: {str(e)}")
            crash_percent, price_in_cents = None, None

        # Generate roast based on crash stats
        try:
            logger.info(f"Generating roast with stats: {crash_percent:.1f}% down, {price_in_cents:.4f}¢")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a savage roast generator for the Nick White Army (NWA).
                        Create brutal roasts about LUX cryptocurrency focusing on technical and project failures.
                        Current stats: Down {crash_percent:.1f}%, price: {price_in_cents:.4f}¢

                        Mix these roasting styles randomly:
                        1. Technical: Mock incompetent programming and development failures
                           - Broken smart contracts and failed deployments
                           - Copy-pasted code and amateur mistakes
                           - Failed code reviews and buggy commits
                        2. Project: Mock LUX's technical disasters and price dumps
                           - Zero liquidity and price crashes
                           - Failed tokenomics and contract bugs
                           - Poor documentation and broken features
                        3. Development: Focus on coding incompetence
                           - Programming jokes and technical puns
                           - Development failure humor
                           - Project disaster mockery

                        Keep roasts under 100 characters. Include emojis (💩,🤡,💻,⚰️,📉,🔥).
                        Make each roast unique and brutal, emphasizing technical failures."""
                    },
                    {
                        "role": "user",
                        "content": "Generate a savage NWA roast about LUX's technical disasters and project failures!"
                    }
                ],
                max_tokens=50,
                temperature=0.9
            )

            roast = response.choices[0].message.content.strip()
            logger.info(f"Generated OpenAI roast: {roast}")
            return roast

        except Exception as e:
            logger.error(f"Error generating roast with OpenAI: {str(e)}")
            fallback = random.choice(FALLBACK_ROASTS)
            logger.info(f"Using fallback roast: {fallback}")
            return fallback

    except Exception as e:
        logger.error(f"Error in roast generation: {str(e)}")
        logger.exception("Full traceback:")
        return random.choice(FALLBACK_ROASTS)