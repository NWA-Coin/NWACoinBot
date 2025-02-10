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
            # Increase font sizes for better visibility
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)  # Increased from 36
            roast_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)  # Increased from 32
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            title_font = roast_font = ImageFont.load_default()

        # Create title based on timeframe
        title = f"$LUX {timeframe} Chart"

        # Text colors and outline settings
        text_color = 'white'
        outline_color = 'black'
        outline_width = 3  # Increased from 2 for better visibility

        # Calculate text dimensions for centering
        title_width = draw.textlength(title, font=title_font)
        roast_width = draw.textlength(roast, font=roast_font)

        # Calculate text heights (approximate)
        title_height = title_font.size
        roast_height = roast_font.size

        # Calculate centered positions
        title_x = (img.width - title_width) / 2
        roast_x = (img.width - roast_width) / 2

        # Adjust vertical positioning
        title_y = 30  # Increased from 20 for better spacing
        roast_y = title_y + title_height + 20  # Dynamic spacing based on title height

        # Draw outline for better text visibility
        for dx in range(-outline_width, outline_width+1):
            for dy in range(-outline_width, outline_width+1):
                if dx != 0 or dy != 0:  # Skip center position
                    draw.text((title_x+dx, title_y+dy), title, font=title_font, fill=outline_color)
                    draw.text((roast_x+dx, roast_y+dy), roast, font=roast_font, fill=outline_color)

        # Draw main text
        draw.text((title_x, title_y), title, font=title_font, fill=text_color)
        draw.text((roast_x, roast_y), roast, font=roast_font, fill=text_color)

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