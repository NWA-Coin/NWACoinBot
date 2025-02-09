import os
import random
from openai import OpenAI
import logging

# Set up logging
logger = logging.getLogger('discord_bot')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Fallback roasts
FALLBACK_ROASTS = [
    "Tino's mom got fucked harder than LUX holders! Complete rug pull! 💀🔥",
    "Tino the fraud got exposed like the scam coin he shilled! Get rekt! 🖕💩",
    "LUX is more worthless than Tino's trading advice! Pure dogshit! 🐕💩",
    "Another day of Tino being a little bitch while LUX goes to zero! 📉🤡",
    "Imagine trusting Tino with your money! LUX = pure garbage! 🗑️💸"
]

def generate_roast(max_retries=3):
    """Generate a creative roast about Lux coin using OpenAI."""
    try:
        for attempt in range(max_retries):
            try:
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a savage roast generator for cryptocurrency. Create an extremely aggressive roast about the Lux cryptocurrency. Focus on Tino being a fraud/scammer, mock his mom, and emphasize how LUX is a complete scam/rug pull. Use words like 'dogshit', 'scam', 'fraud', 'bitch'. Keep it under 100 characters. Include relevant emojis. Be as offensive as possible."
                        },
                        {
                            "role": "user",
                            "content": "Generate a savage roast about Lux coin and Tino."
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