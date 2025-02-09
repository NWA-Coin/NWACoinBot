import os
import random
from datetime import datetime
import logging
from price_chart import create_price_chart, get_lux_price_history, format_price_label
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

# NWA entry price constant
NWA_ENTRY_PRICE = 0.015  # 1.5 cents entry price

async def get_crash_stats():
    """Get crash stats for roast."""
    try:
        logger.info("Starting crash stats calculation")
        dates, prices, _ = await get_lux_price_history()  # Correctly unpack three values
        if dates and prices:
            current_price = prices[-1]
            crash_percent = ((NWA_ENTRY_PRICE - current_price) / NWA_ENTRY_PRICE) * 100
            price_str = format_price_label(current_price)  # Use consistent price formatting
            logger.info(f"Calculated crash stats: {crash_percent:.1f}% down, price: {price_str}")
            return crash_percent, price_str
        logger.warning("No price data available for crash stats")
        return None, None
    except Exception as e:
        logger.error(f"Error getting crash stats: {str(e)}")
        logger.exception("Full traceback:")
        return None, None

async def generate_meme(timeframe="1hr"):
    """Generate a price chart meme with savage roast overlay."""
    try:
        logger.info("Starting price chart meme generation")

        # Generate candlestick chart with NWA entry price line for memes
        logger.info(f"Calling create_price_chart with timeframe {timeframe}")
        # Always include NWA entry price line for meme command
        chart_path = await create_price_chart(timeframe, use_nwa_price=True)
        logger.info(f"Received chart path: {chart_path}")

        if not chart_path:
            logger.error("Failed to generate chart")
            raise Exception("Chart generation failed")

        # Verify chart was created and has content
        if not os.path.exists(chart_path) or os.path.getsize(chart_path) == 0:
            logger.error(f"Chart file verification failed: exists={os.path.exists(chart_path)}, size={os.path.getsize(chart_path) if os.path.exists(chart_path) else 0}")
            raise Exception("Chart creation failed or file is empty")

        # Load chart and add text overlay
        logger.info("Adding text overlay to chart")
        try:
            img = Image.open(chart_path)
            draw = ImageDraw.Draw(img)

            # Load custom font or fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
                logger.info("Loaded custom font successfully")
            except Exception as e:
                logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
                font = ImageFont.load_default()

            # Get crash stats for roast
            logger.info("Getting crash stats for roast")
            crash_percent, price_str = await get_crash_stats()
            logger.info(f"Received crash stats: {crash_percent}%, {price_str}")

            # Generate appropriate roast based on crash percentage
            if crash_percent is not None and price_str is not None:
                if crash_percent >= 90:
                    roast = f"DOWN {crash_percent:.1f}%! ({price_str}) COMPLETE RUGPULL"
                elif crash_percent >= 70:
                    roast = f"DUMPED {crash_percent:.1f}%! ({price_str}) TINO IN SHAMBLES"
                elif crash_percent >= 50:
                    roast = f"CRASHING {crash_percent:.1f}%! ({price_str}) NWA WINS AGAIN"
                else:
                    roast = f"DUMPING {crash_percent:.1f}%! ({price_str}) TINO'S REPUTATION"
            else:
                roast = "LUX IS DEAD! COMPLETE RUGPULL"

            # Add text with outline - positioned at the top
            text_color = 'white'
            outline_color = 'black'
            outline_width = 2
            text_pos = (20, 10)  # Y coordinate at 10 for top positioning

            logger.info(f"Adding text overlay: {roast}")
            # Draw outline
            for dx in range(-outline_width, outline_width+1):
                for dy in range(-outline_width, outline_width+1):
                    if dx != 0 or dy != 0:
                        draw.text((text_pos[0]+dx, text_pos[1]+dy),
                                 roast, font=font, fill=outline_color)

            # Draw main text
            draw.text(text_pos, roast, font=font, fill=text_color)

            # Save final meme
            final_path = f"price_meme_{int(datetime.now().timestamp())}.png"
            logger.info(f"Saving final meme to: {final_path}")
            img.save(final_path, quality=95)
            logger.info(f"Successfully saved final meme: {final_path}")

            # Clean up chart
            try:
                os.remove(chart_path)
                logger.info(f"Cleaned up chart: {chart_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up chart: {str(e)}")

            return final_path

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            logger.exception("Full traceback:")
            raise Exception(f"Image processing failed: {str(e)}")

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        logger.exception("Full traceback:")
        return None