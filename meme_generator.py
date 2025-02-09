import os
import random
from datetime import datetime
import logging
from price_chart import create_price_chart, format_price_label
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logger = logging.getLogger('discord_bot')

async def generate_meme(timeframe="1hr"):
    """Generate a price chart meme with savage roast overlay."""
    try:
        logger.info(f"Starting meme generation with timeframe {timeframe}")

        # Generate price chart and get price data
        chart_path, timestamps, prices = await create_price_chart(timeframe)
        if not chart_path or not timestamps or not prices:
            logger.error("Failed to generate chart")
            raise Exception("Chart generation failed")

        # Calculate percentages
        entry_price = 0.015  # NWA entry price
        current_price = prices[-1]
        start_price = prices[0]

        # Calculate total crash from entry (always positive when price goes down)
        crash_percent = ((entry_price - current_price) / entry_price) * 100

        # Calculate timeframe change (negative when price goes down)
        timeframe_change = ((current_price - start_price) / start_price) * 100

        price_str = format_price_label(current_price)
        logger.info(f"Price data: start=${start_price:.6f}, current=${current_price:.6f}")
        logger.info(f"Calculated stats: Total crash={crash_percent:.1f}%, Timeframe change={timeframe_change:.1f}%, Price={price_str}")

        # Add text overlay
        img = Image.open(chart_path)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            font = ImageFont.load_default()

        # Format timeframe text (showing actual price movement)
        timeframe_text = f"({timeframe_change:+.1f}% in {timeframe})"

        # Generate roast based on crash percentage
        if crash_percent >= 90:
            roast = f"DOWN {crash_percent:.1f}%! COMPLETE RUGPULL! ({price_str})"
        elif crash_percent >= 70:
            roast = f"DUMPED {crash_percent:.1f}%! SINCE NWA TAKEOVER! ({price_str})"
        elif crash_percent >= 50:
            roast = f"CRASHING {crash_percent:.1f}%! NWA WINS AGAIN! ({price_str})"
        else:
            roast = f"DUMPING {crash_percent:.1f}%! SINCE NWA TAKEOVER! ({price_str})"

        logger.info(f"Generated roast text: {roast}")

        # Add text with outline
        text_color = 'white'
        outline_color = 'black'
        outline_width = 2
        text_pos = (20, 10)

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

        # Clean up temporary files
        try:
            os.remove(chart_path)
            logger.info(f"Cleaned up chart: {chart_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up chart: {str(e)}")

        return final_path

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        logger.exception("Full traceback:")
        return None