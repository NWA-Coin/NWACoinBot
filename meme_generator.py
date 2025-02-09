import os
import random
from datetime import datetime
import logging
from price_chart import create_price_chart, get_lux_price_history
from PIL import Image, ImageDraw, ImageFont
import asyncio

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

        # Generate chart using matplotlib
        chart_path = create_price_chart()
        if not chart_path:
            logger.error("Failed to generate chart")
            raise Exception("Chart generation failed")

        # Verify chart was created and has content
        if not os.path.exists(chart_path) or os.path.getsize(chart_path) == 0:
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            dates, prices = loop.run_until_complete(get_lux_price_history())
            loop.close()

            if dates and prices:
                entry_price = 0.015  # NWA entry price
                current_price = prices[-1]
                crash_percent = ((entry_price - current_price) / entry_price) * 100
                price_in_cents = current_price * 100
                logger.info(f"Calculated crash stats: {crash_percent:.1f}% down, price: {price_in_cents:.4f}¢")

                if crash_percent >= 90:
                    roast = f"DOWN {crash_percent:.1f}%! ({price_in_cents:.4f}¢) COMPLETE RUGPULL! 💀"
                elif crash_percent >= 70:
                    roast = f"DUMPED {crash_percent:.1f}%! ({price_in_cents:.4f}¢) TINO IN SHAMBLES! 🖕"
                elif crash_percent >= 50:
                    roast = f"CRASHING {crash_percent:.1f}%! ({price_in_cents:.4f}¢) NWA WINS AGAIN! 🔥"
                else:
                    roast = f"DUMPING {crash_percent:.1f}%! ({price_in_cents:.4f}¢) TINO'S REPUTATION! 💸"
            else:
                roast = "LUX IS DEAD! COMPLETE RUGPULL! 💀"

            # Add text with outline
            text_color = 'white'
            outline_color = 'black'
            outline_width = 2
            text_pos = (20, 20)

            logger.info("Adding text overlay with outline")
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
            raise Exception(f"Image processing failed: {str(e)}")

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        logger.exception("Full traceback:")
        return None