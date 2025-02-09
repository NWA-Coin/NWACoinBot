import os
import random
from openai import OpenAI
from price_chart import fetch_current_price
import logging

# Set up logging
logger = logging.getLogger('discord_bot')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Fallback roasts with NWA references
FALLBACK_ROASTS = [
    "Straight Outta Value! LUX dropping harder than NWA's basslines! 🎤💀",
    "LUX got less value than a bootleg tape from Compton! Pure Trash! 📉🎵",
    "Even Ice Cube thinks LUX's price is too cold! Complete Garbage! 🧊💸",
    "LUX just got more rekt than Eazy-E's competition! You Got Nothing! 🎤💥",
    "LUX chart looking like it got stomped by the whole crew! Get Rekt! 👊💀",
    "Down so bad even Dr. Dre can't mix this shit right! Complete Trash! 🎧📉",
    "Your investment's more fucked than Death Row Records! Pure Garbage! ⚰️💀"
]

def get_price_roast():
    """Generate a price-specific roast based on current performance."""
    try:
        price, change = fetch_current_price()
        if price < 0.01:  # Changed threshold to be more realistic
            return f"LUX worth less than NWA's first demo tape! ${price:.4f} - Pure Garbage! 💀"
        elif change < -5:  # More realistic threshold for negative change
            return f"Down BAD! LUX getting destroyed like it's on Death Row! Complete Trash! ⚰️"
        return None
    except Exception as e:
        logger.error(f"Error getting price roast: {str(e)}")
        return None

def generate_roast(max_retries=3):
    """Generate a creative roast about Lux coin using OpenAI."""
    try:
        # Try to get a price-based roast first
        price_roast = get_price_roast()
        if price_roast:
            logger.info(f"Using price-based roast: {price_roast}")
            return price_roast

        # Get current price for context
        price, change = fetch_current_price()

        for attempt in range(max_retries):
            try:
                # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a savage roast generator for cryptocurrency. Create an extremely aggressive, vulgar roast about the Lux cryptocurrency that references NWA, gangsta rap, and its terrible performance. Make it extremely harsh and vulgar. Use words like 'trash', 'garbage', 'worthless', 'rekt'. Keep it under 100 characters. Include relevant emojis."
                        },
                        {
                            "role": "user",
                            "content": f"Generate a savage roast about Lux coin. Current price: ${price:.4f}, 24h change: {change}%"
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