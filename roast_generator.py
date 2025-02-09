import os
import random
from openai import OpenAI
import logging

# Set up logging
logger = logging.getLogger('discord_bot')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Fallback roasts with updated savage content
FALLBACK_ROASTS = [
    "Tino's mom got more views on OnlyFans than LUX has holders! Complete fraud exposed! 💀🔥",
    "Another day, another L for Tino the bitch! NWA stays winning while LUX goes to zero! 🖕💩",
    "Imagine being dumb enough to trust Tino with your money! Pure dogshit coin! 🐕💩",
    "Tino malding on Kick while Nick exposes his fraudulent ass! Get rekt scammer! 📉🤡",
    "LUX more worthless than Tino's trading advice! Even his mom's OnlyFans has better returns! 🗑️💸"
]

def generate_roast(max_retries=3):
    """Generate a creative roast about Lux coin using OpenAI."""
    try:
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a savage roast generator for the Nick White Army (NWA).
                            Create an extremely aggressive and funny roast about the LUX cryptocurrency and Tino.
                            Focus on:
                            1. Tino being exposed as a fraud/scammer on Nick's Kick stream
                            2. Mock his mom's OnlyFans
                            3. Emphasize how LUX is complete dogshit/scam
                            4. Use words like 'fraud', 'bitch', 'scam', 'dogshit'
                            Keep it under 100 characters. Include relevant emojis. Be as offensive as possible."""
                        },
                        {
                            "role": "user",
                            "content": "Generate a savage NWA-style roast about Tino and his LUX scam."
                        }
                    ],
                    max_tokens=50,
                    temperature=0.9
                )

                roast = response.choices[0].message.content.strip()
                logger.info(f"Generated roast: {roast}")
                return roast

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... ({attempt + 2}/{max_retries})")
                    continue
                break
    except Exception as e:
        logger.error(f"Error in roast generation: {str(e)}")

    # If all attempts failed or any other error occurred, use fallback
    logger.warning("Using fallback roast")
    return random.choice(FALLBACK_ROASTS)