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

# Technical and code-focused fallback roasts
FALLBACK_ROASTS = [
    # Technical/Code Roasts
    "LUX code looking like a bootcamp dropout's first project! Complete disaster! 💩👨‍💻",
    "Tino can't even code a proper rugpull! NWA exposing this fraud! 🔥🤡",
    "Another day of LUX smart contracts failing! Trash coder exposed! 🗑️💀",
    "Stack Overflow won't save your shitcoin Tino! Complete failure! ⚰️👨‍💻",
    "Error 404: Tino's coding skills not found! NWA stays winning! 🏆💯",
    "Copy-pasting code won't save LUX! Another L for this fraud! 📝🗑️",
    "Even ChatGPT writes better code than Tino! Complete failure! 🤖⚰️",

    # Personal/Funny Roasts
    "Tino malding while NWA keeps winning! Another day of pure humiliation! 🤡🖕",
    "LUX chart looking like Tino's credibility - straight to zero! 📉💩",
    "NWA raw dogging Tino's reputation while LUX dumps! Complete disaster! 🔥💀",
    "Even your trading bot dumped LUX! Get exposed fraud! 🤖🗑️",
    "Tino begging ChatGPT to pump LUX! Pathetic scammer! 🤮💸",

    # Pronouns/Identity Roasts
    "They/Them got THEY ass exposed by NWA! Complete disaster! 🏳️‍🌈💀",
    "THEY thought LUX would moon but THEIR bags went to zero! 🌈📉",
    "They/Them can't even code THEIR way out of this rugpull! 🏳️‍🌈🤡",
    "THEIR GitHub commits looking more dead than LUX price! 💻⚰️",
    "They/Them getting exposed while NWA stays winning! 🌈🔥",

    # Mixed Content
    "They/Them's code + zero liquidity = complete disaster! 🏳️‍🌈💩",
    "Error in THEIR trading bot: exit_scam.py failed! 🤖📉",
    "NWA exposing THEIR copy-pasted code! Another L! 🔥💻",
    "They/Them can't debug THEIR way out of this one! 🌈🐛"
]

async def get_crash_stats():
    """Get crash stats for roast."""
    try:
        dates, prices = await get_lux_price_history()
        if dates and prices:
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

def generate_roast():
    """Generate a savage roast with OpenAI, mixing technical, personal, and pronoun content."""
    try:
        logger.info("Starting roast generation")

        # Create new event loop for async operations
        try:
            crash_percent, price_in_cents = asyncio.run(get_crash_stats())
        except RuntimeError:
            # If running inside Discord's event loop, use a different approach
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            crash_percent, price_in_cents = loop.run_until_complete(get_crash_stats())
            loop.close()

        # Generate roast based on crash stats
        try:
            logger.info(f"Generating roast (attempt 1/3)")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a savage roast generator for the Nick White Army (NWA).
                        Create diverse roasts about LUX cryptocurrency and Tino (who uses they/them pronouns).
                        Current stats: Down {crash_percent:.1f}%, price: {price_in_cents:.4f}¢

                        Mix these roasting styles randomly:
                        1. Technical: Mock their incompetent programming and development failures
                        2. Personal: Roast their trading failures and reputation
                        3. Identity: Use they/them pronouns creatively in roasts (THEY/THEM in caps)
                        4. Project: Mock LUX's technical disasters and price dumps

                        Keep roasts under 100 characters. Include emojis (💩,🤡,💻,⚰️,📉,🌈).
                        Make each roast unique and savage, emphasizing NWA's dominance."""
                    },
                    {
                        "role": "user",
                        "content": "Generate a savage NWA roast mixing technical failures, personal mockery, and they/them pronouns!"
                    }
                ],
                max_tokens=50,
                temperature=0.9
            )

            roast = response.choices[0].message.content.strip()
            logger.info(f"Generated roast: {roast}")
            return roast

        except Exception as e:
            logger.error(f"Error generating roast with OpenAI: {str(e)}")
            return random.choice(FALLBACK_ROASTS)

    except Exception as e:
        logger.error(f"Error in roast generation: {str(e)}")
        logger.exception("Full traceback:")
        return random.choice(FALLBACK_ROASTS)