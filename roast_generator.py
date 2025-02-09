import os
import random
from openai import OpenAI
import logging

# Set up logging
logger = logging.getLogger('discord_bot')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Fallback roasts with more aggressive NWA content
FALLBACK_ROASTS = [
    "Tino's mom spreading it wider than LUX's rugpull! NWA wins again! 💦🖕",
    "Another day of Tino crying while his mom's OF pays for his losses! Get rekt bitch! 🤡💸",
    "Tino's mom making more on OF than his dogshit coin ever will! Fraud exposed! 🍑💩",
    "NWA raw dogging Tino's reputation while LUX goes to zero! Complete fucking disaster! 🔥💀",
    "Imagine trusting this bitchass scammer Tino! Even his mom knows LUX is pure fucking garbage! 🗑️🤮"
]

def generate_roast(max_retries=3):
    """Generate an aggressive roast about Lux coin using OpenAI."""
    try:
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating roast (attempt {attempt + 1}/{max_retries})")
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                # do not change this unless explicitly requested by the user
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a savage roast generator for the Nick White Army (NWA).
                            Create an extremely aggressive and offensive roast about LUX cryptocurrency and Tino.
                            Be as savage as possible focusing on:
                            1. Tino being a complete bitch and getting exposed as fraud on Nick's Kick stream
                            2. Make explicit references to his mom's OnlyFans content
                            3. Mock LUX as a complete scam/rugpull/dogshit project
                            4. Emphasize how NWA keeps raw dogging Tino's reputation
                            Use aggressive words like 'bitch', 'fraud', 'scam', 'dogshit', 'fucking garbage'
                            Keep it under 100 characters. Include offensive emojis. Be as brutal as possible."""
                        },
                        {
                            "role": "user",
                            "content": "Generate the most savage NWA-style roast about that fraud Tino and his scam coin LUX."
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