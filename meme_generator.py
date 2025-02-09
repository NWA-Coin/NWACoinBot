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
        logger.debug("Calling create_price_chart()")
        meme_path = create_price_chart()

        if not meme_path:
            logger.error("Failed to generate price chart meme - create_price_chart returned None")
            return "Failed to generate chart! Probably as dead as LUX's future! 💀"

        if not os.path.exists(meme_path):
            logger.error(f"Generated meme file does not exist at path: {meme_path}")
            return "Chart generation failed! As reliable as Tino's promises! 💀"

        file_size = os.path.getsize(meme_path)
        logger.info(f"Successfully generated price chart meme: {meme_path} (size: {file_size} bytes)")
        return meme_path

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        logger.exception("Full traceback:")
        return "Chart's too dead to generate! Just like Tino's reputation! 💀"