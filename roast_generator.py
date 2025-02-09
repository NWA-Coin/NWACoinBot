import os
import random
from openai import OpenAI
from price_chart import fetch_current_price
import logging

# Set up logging
logger = logging.getLogger('discord_bot')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# More aggressive fallback roasts with NWA references
FALLBACK_ROASTS = [
    "Straight Outta Value! LUX dropping harder than NWA's basslines! 🎤💀",
    "LUX got less value than a bootleg tape from Compton swap meet! Your shit's WORTHLESS! 📉🎵",
    "Even Ice Cube thinks LUX's price is too cold! Straight Outta Profits, Straight Into The Trash! 🧊💸",
    "LUX just got more rekt than Eazy-E's competition! You Ain't Worth Shit! 🎤💥",
    "LUX chart looking like it got stomped by the whole NWA crew! Get Rekt! 👊💀",
    "Straight Outta Money! This coin's performing worse than MC Ren's solo career! 📉🎤",
    "Your shit's more dead than Death Row Records! WORTHLESS! ⚰️💀",
    "Portfolio lookin' like it got stomped by the whole Compton crew! Get Rekt! 👟💰",
    "More worthless than a Vanilla Ice concert in Compton! Pure Garbage! 🧊💸",
    "Down so bad even Dr. Dre can't mix this shit right! Complete Trash! 🎧📉",
    "LUX weaker than DJ Yella's solo album sales! Pure Garbage! 🎵💩",
    "Your investment's more fucked than Easy-E's record label! Get Rekt! 💀📉",
    "Charts redder than Blood Walk in Compton! You Got NOTHING! 🩸💀",
    "LUX performing worse than NWA's reunion attempts! Pure Trash! 🎤📉"
]

def get_price_roast():
    """Generate a price-specific roast based on current performance."""
    try:
        price, change = fetch_current_price()
        if price < 0.0001:
            return f"LUX worth less than NWA's first demo tape! ${price:.12f} - Pure Garbage! 💀"
        elif change < -10 or change == -99.99:
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
                    model="gpt-4o",  # Using the latest model for better roasts
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a savage roast generator for cryptocurrency. Create an extremely aggressive, vulgar roast about the Lux cryptocurrency that references NWA, gangsta rap, and its terrible performance. Make it extremely harsh and vulgar. Use words like "trash", "garbage", "worthless", "rekt". Keep it under 100 characters. Include relevant emojis. Use street slang and make it as disrespectful as possible."""
                        },
                        {
                            "role": "user",
                            "content": f"Generate a savage roast about Lux coin. Current price: ${price:.12f}, 24h change: {change if change != -99.99 else 'unknown (probably rekt)'}%"
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

        # If all retries failed or no price data, use fallback
        logger.warning("Using fallback roast due to API/price fetch failure")
        return random.choice(FALLBACK_ROASTS)
    except Exception as e:
        logger.error(f"Error in roast generation: {str(e)}")
        return random.choice(FALLBACK_ROASTS)