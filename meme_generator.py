import os
import random
from datetime import datetime
import logging
from price_chart import create_price_chart, format_price_label
from PIL import Image, ImageDraw, ImageFont
import asyncio
from roast_generator import generate_roast

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

        # Generate a fresh roast for this meme
        roast = await generate_roast()
        logger.info(f"Generated roast for meme: {roast}")

        # Add text overlay
        img = Image.open(chart_path)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            font = ImageFont.load_default()

        # Create title based on timeframe
        title = f"$LUX {timeframe} Chart"

        # Add text with outline
        text_color = 'white'
        outline_color = 'black'
        outline_width = 2

        # Center the title and roast text
        title_width = draw.textlength(title, font=font)
        roast_width = draw.textlength(roast, font=font)

        # Calculate centered positions
        title_x = (img.width - title_width) / 2
        roast_x = (img.width - roast_width) / 2

        # Position for title and roast
        title_pos = (title_x, 10)
        roast_pos = (roast_x, 50)

        # Draw outline and text for title
        for dx in range(-outline_width, outline_width+1):
            for dy in range(-outline_width, outline_width+1):
                if dx != 0 or dy != 0:
                    draw.text((title_pos[0]+dx, title_pos[1]+dy),
                            title, font=font, fill=outline_color)
                    draw.text((roast_pos[0]+dx, roast_pos[1]+dy),
                            roast, font=font, fill=outline_color)

        # Draw main text
        draw.text(title_pos, title, font=font, fill=text_color)
        draw.text(roast_pos, roast, font=font, fill=text_color)

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