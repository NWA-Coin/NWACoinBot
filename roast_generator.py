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
    "Your shitty code looks like it was written by a drunk monkey! Complete disaster! 🤮💩",
    "Can't even code a proper rugpull you incompetent f*ck! NWA destroying you! 🔥💀",
    "Another day of your garbage smart contracts failing! Get rekt trash dev! 🗑️💩",
    "Stack Overflow won't save your worthless shitcoin! Complete failure! ⚰️👨‍💻",
    "Error 404: Coding skills not found, just like your liquidity! 📉💀",
    "Copy-pasting code won't save your worthless token! Another L! 🗑️🤡",
    "Even a brain-dead monkey codes better! Complete failure! 🐒💩",
    "Your GitHub is full of stolen garbage! Certified fraud! 💩🖕",
    "Imagine failing basic syntax you absolute moron! Get exposed! 🤡💻",
    "Senior dev? More like senior dumbass! Pure trash! 🗑️👨‍💻",

    # Project/Price Roasts
    "LUX chart looking like your life - straight to the dumpster! 📉🗑️",
    "NWA destroying your reputation while your mom dumps LUX! 🔥💀",
    "Even your trading bot dumped this garbage! Get exposed fraud! 🤖🖕",
    "Begging ChatGPT to pump your worthless token! Pathetic loser! 🤮💸",
    "Another day, another LUX dump! NWA stays winning you clown! 🤡💩",
    "Zero liquidity just like your brain cells! Complete disaster! 💸📉",
    "Imagine launching a token that only goes down! Certified moron! 😂🗑️",
    "Your token's more dead than your dev career! Get rekt! ⚰️💩",
    "Chart's dropping faster than your IQ! Complete failure! 📉🤡",
    "Even LUNA had better tokenomics! Absolute disaster! 💩💸",

    # Mixed Content
    "Failed code + zero liquidity = complete dumpster fire! 💩📉",
    "Error in rugpull.py: exit_scam.failed()! Too stupid to scam! 🤖⚰️",
    "NWA exposing your copy-pasted garbage! Stay getting rekt! 🔥💩",
    "Can't debug your way out of being trash! Complete failure! 💻🗑️",
    "Pushed to main and the price crashed again! Certified clown! 🤡💩",
    "From junior dev to complete laughingstock! Stay losing trash! 🖕👨‍💻",
    "Commit history: 100% stolen garbage! Pure trash! 💩🤮",
    "Your code's more useless than SAFEMOON! Complete joke! 🤡💩",
    "Even BITCONNECT had better devs! Absolute failure! 💩📉",
    "Bootcamp dropout writing rugpull code! Get exposed! 🗑️👨‍💻"
]

# Add new fallback roasts specifically targeting Nick White
NICK_WHITE_ROASTS = [
    "Virgin Nick White still living in mommy's basement! Complete loser! 🤡💩",
    "Yo Nick White, did your mom buy you those programming socks? Pathetic virgin! 🧦🤮",
    "Nick White the type to practice leetcode while his girl's out with Chad! Oh wait... 🤡💀",
    "Even ChatGPT writes better code than Nick White! Certified clown! 🤖🗑️",
    "Nick White's YouTube career is more dead than his social life! 📉💩",
    "Imagine being a 30-year-old virgin teaching basic loops! Get rekt Nick! 👶🤡",
    "Nick White's code reviews take longer than his dating history! Complete L! 💀🖕",
    "Hey Nick, your mom called - she wants her basement back! 🏠🤮",
    "Nick White the type to debug his social skills and still fail! 🐛💩",
    "Even LUNA had better documentation than Nick's dating profile! 📝🤡"
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
                        "content": f"""You are an extremely savage and vulgar roast generator for the Nick White Army (NWA).
                        Create brutal, vulgar roasts mixing insults about Nick White and the LUX cryptocurrency.
                        Current stats: Down {crash_percent:.1f}%, price: {price_in_cents:.4f}¢

                        Mix these brutal roasting styles:
                        1. Nick White Personal Roasts:
                           - Mock his virgin status and living situation
                           - Roast his basic programming tutorials
                           - Make fun of his nonexistent social life
                           - Blast his failed YouTube career
                        2. Technical Roasts:
                           - Mock their incompetent coding and development disasters
                           - Roast their broken smart contracts and failed deployments
                           - Make fun of their copy-pasted code and amateur mistakes
                        3. Price/Project Roasts:
                           - Mock their constant price dumps and zero liquidity
                           - Roast their failed tokenomics and contract bugs

                        Guidelines:
                        - Keep roasts under 100 characters
                        - Include emojis (💩,🤡,💻,⚰️,📉,🔥,🖕,🤮)
                        - Be extremely vulgar and brutal
                        - Focus on Nick's virgin status and technical failures
                        - Make each roast unique and devastating"""
                    },
                    {
                        "role": "user",
                        "content": "Generate the most savage, vulgar NWA roast about Nick White and LUX's disasters!"
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
            # Use Nick White specific fallback roasts
            fallback = random.choice(FALLBACK_ROASTS + NICK_WHITE_ROASTS)
            logger.info(f"Using fallback roast: {fallback}")
            return fallback

    except Exception as e:
        logger.error(f"Error in roast generation: {str(e)}")
        logger.exception("Full traceback:")
        return random.choice(FALLBACK_ROASTS + NICK_WHITE_ROASTS)