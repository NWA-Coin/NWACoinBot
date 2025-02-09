import os
import random
from datetime import datetime
import logging
from price_chart import create_price_chart

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

def generate_meme():
    """Generate a price chart meme with savage roast overlay."""
    try:
        logger.info("Starting price chart meme generation")

        # Generate price chart with roast
        meme_path = create_price_chart()

        if not meme_path:
            logger.error("Failed to generate price chart meme")
            return "Failed to generate chart! Probably as dead as LUX's future! 💀"

        logger.info(f"Successfully generated price chart meme: {meme_path}")
        return meme_path

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        return "Chart's too dead to generate! Just like Tino's reputation! 💀"