import os
import random
import logging
from openai import OpenAI

# Set up logging
logger = logging.getLogger('discord_bot')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Components for dynamic roast generation
NICK_TRAITS = [
    "fat rat",
    "lazy",
    "fat boy",
    "virgin",
    "failed streamer"
]

NICK_ACTIONS = [
    "still living in mommy's basement",
    "can't even code his way out of being fat",
    "teaching basic while loops",
    "struggling with for loops",
    "making tutorial videos nobody watches",
    "debugging his McDonald's order",
    "trying to optimize his diet plan",
    "explaining variables to zero viewers"
]

NICK_CONSEQUENCES = [
    "Complete loser",
    "Total failure", 
    "Exposed fraud",
    "Get rekt",
    "Stay losing",
    "Pure trash"
]

NICK_EMOJIS = ["🐀", "🍔", "📺", "💩", "🤡", "💻", "💀", "🤮", "🐷", "👶", "⌨️", "🧦"]

# Fallback roasts for error cases
FALLBACK_ROASTS = [
    "Fat rat Nick White still living in mommy's basement! Complete loser! 🐀💩",
    "Nick White so lazy he can't even code his way out of being fat! 🍔🤮",
    "Yo fat boy Nick, did your mom buy those XXXL programming socks? 🧦🐷",
    "Nick White's viewcount lower than his IQ! Failed streamer confirmed! 📺🗑️",
    "Nick White's Twitch career more dead than his diet plans! 🍕💀",
    "Lazy ass Nick White can't even debug his eating habits! Get rekt! 🍔🤡",
    "Nick the rat got exposed! Back to making basic loop tutorials! 🐀👶",
    "Fat boy's keyboard greasier than his code quality! 🍔⌨️"
]

def generate_dynamic_roast():
    """Generate a dynamic roast using OpenAI"""
    try:
        # Create a prompt that focuses on Nick's traits
        prompt = """Generate a brutal, savage roast about Nick White with these traits:
        - Being fat and lazy
        - Failed streaming career (no viewers)
        - Living in his mom's basement
        - Teaching basic programming concepts

        Rules:
        - Keep it under 100 characters
        - Include 2 emojis from: 🐀🍔📺💩🤡💻💀🤮🐷👶⌨️
        - Focus only on personal traits
        - Make it unique and devastating
        - NO mentions of cryptocurrency or coding quality
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Generate a savage roast about Nick White!"}
            ],
            max_tokens=60,
            temperature=0.9
        )

        roast = response.choices[0].message.content.strip()
        logger.info(f"Generated OpenAI roast: {roast}")
        return roast

    except Exception as e:
        logger.error(f"Error generating dynamic roast: {str(e)}")
        return None

async def generate_roast(is_nick_roast=False):
    """Generate a savage roast focusing on Nick White's traits"""
    try:
        logger.info("Starting roast generation")

        if is_nick_roast:
            # Try to generate a dynamic roast first
            roast = generate_dynamic_roast()
            if roast:
                logger.info(f"Generated dynamic roast: {roast}")
                return roast

            # Fallback to pre-written roasts if dynamic generation fails
            fallback = random.choice(FALLBACK_ROASTS)
            logger.info(f"Using fallback roast: {fallback}")
            return fallback
        else:
            # For non-Nick roasts, return a generic technical roast
            return "Your code looks like it was written by a drunk monkey! Complete disaster! 🤮💩"

    except Exception as e:
        logger.error(f"Error in roast generation: {str(e)}")
        logger.exception("Full traceback:")
        return random.choice(FALLBACK_ROASTS)