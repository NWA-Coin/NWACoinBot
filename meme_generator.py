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

async def get_crash_stats():
    """Get crash stats for roast."""
    try:
        logger.info("Starting crash stats calculation")
        timestamps, prices = await get_lux_price_history()
        if timestamps and prices:
            entry_price = 0.015  # NWA entry price
            current_price = prices[-1]
            # Calculate total crash from entry
            crash_percent = ((entry_price - current_price) / entry_price) * 100
            price_in_cents = current_price * 100
            logger.info(f"Calculated crash stats: {crash_percent:.1f}% down, price: {price_in_cents:.4f}¢")

            # Calculate timeframe change using first and last price in current view
            start_price = prices[0]  # First price in the timeframe
            end_price = prices[-1]   # Last price in the timeframe
            timeframe_drop = ((start_price - end_price) / start_price) * 100 if start_price != 0 else 0

            logger.info(f"Timeframe price change: start={start_price:.6f}, end={end_price:.6f}, change={timeframe_drop:.1f}%")
            return crash_percent, format_price_label(current_price), timeframe_drop
        logger.warning("No price data available for crash stats")
        return None, None, None
    except Exception as e:
        logger.error(f"Error getting crash stats: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None

async def generate_meme(timeframe="1hr"):
    """Generate a price chart meme with savage roast overlay."""
    try:
        logger.info(f"Starting meme generation with timeframe {timeframe}")

        # Generate price chart
        chart_path = await create_price_chart(timeframe)
        if not chart_path:
            logger.error("Failed to generate chart")
            raise Exception("Chart generation failed")

        # Verify chart exists and has content
        if not os.path.exists(chart_path) or os.path.getsize(chart_path) == 0:
            logger.error(f"Chart file verification failed: exists={os.path.exists(chart_path)}, size={os.path.getsize(chart_path) if os.path.exists(chart_path) else 0}")
            raise Exception("Chart creation failed or file is empty")

        # Add text overlay
        logger.info("Adding text overlay to chart")
        try:
            img = Image.open(chart_path)
            draw = ImageDraw.Draw(img)

            # Load custom font or fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            except Exception as e:
                logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
                font = ImageFont.load_default()

            # Get crash stats for roast - consolidate the data fetching
            crash_percent, price_str, timeframe_drop = await get_crash_stats()

            # Generate roast based on crash percentage and timeframe drop
            if crash_percent is not None and price_str is not None:
                # Format timeframe text with sign
                sign = "-" if timeframe_drop > 0 else "+"  # Reverse sign since drop is positive when price decreases
                timeframe_text = f"({sign}{abs(timeframe_drop):.1f}% in {timeframe})"

                if crash_percent >= 90:
                    roast = f"DOWN {crash_percent:.1f}%! {timeframe_text} ({price_str}) COMPLETE RUGPULL"
                elif crash_percent >= 70:
                    roast = f"DUMPED {crash_percent:.1f}%! {timeframe_text} ({price_str}) TINO IN SHAMBLES"
                elif crash_percent >= 50:
                    roast = f"CRASHING {crash_percent:.1f}%! {timeframe_text} ({price_str}) NWA WINS AGAIN"
                else:
                    roast = f"DUMPING {crash_percent:.1f}%! {timeframe_text} ({price_str}) TINO'S REPUTATION"
            else:
                roast = "LUX IS DEAD! COMPLETE RUGPULL"

            # Add text with outline at the top
            text_color = 'white'
            outline_color = 'black'
            outline_width = 2
            text_pos = (20, 10)

            logger.info(f"Adding text overlay: {roast}")
            # Draw outline
            for dx in range(-outline_width, outline_width+1):
                for dy in range(-outline_width, outline_width+1):
                    if dx != 0 or dy != 0:
                        draw.text((text_pos[0]+dx, text_pos[1]+dy),
                                roast, font=font, fill=outline_color)

            # Draw main text
            draw.text(text_pos, roast, font=font, fill=text_color)

            # Save final meme with high quality
            final_path = f"price_meme_{int(datetime.now().timestamp())}.png"
            img.save(final_path, quality=95)
            logger.info(f"Successfully saved final meme: {final_path}")

            # Clean up the temporary chart file
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