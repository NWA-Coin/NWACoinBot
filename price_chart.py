import os
import logging
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont
from market_data import fetch_market_data  # Updated import
import math

# Set up logging
logger = logging.getLogger('discord_bot')

# Define Eastern timezone
eastern = pytz.timezone('US/Eastern')

def round_to_nice_number(value):
    """Round to a nice number for display."""
    magnitude = math.floor(math.log10(value))
    power_of_ten = 10 ** magnitude
    normalized = value / power_of_ten

    nice_numbers = [1, 2, 5, 10]
    nice_normalized = min(nice_numbers, key=lambda x: abs(x - normalized))

    return nice_normalized * power_of_ten

def format_price_label(price):
    """Format price in cents."""
    cents = price * 100
    return f"{cents:.2f}¢"

def format_time_label(timestamp, timeframe):
    """Format time label based on timeframe, returning separate time and date components."""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, pytz.UTC)
        eastern_time = dt.astimezone(eastern)

        # Initialize default values
        time_str = ""
        date_str = eastern_time.strftime("%m/%d")  # Always show date

        # Set time string based on timeframe
        if timeframe in ["5m", "15m", "1hr"]:
            time_str = eastern_time.strftime("%-I:%M %p")
        elif timeframe == "24hr":
            time_str = eastern_time.strftime("%-I%p")
        elif timeframe == "7d":
            time_str = eastern_time.strftime("%a")
        # For 1m and 3m, time_str remains empty as initialized

        return time_str, date_str
    except Exception as e:
        logger.error(f"Error formatting time label: {str(e)}")
        return "", "N/A"  # Return safe defaults on error

async def get_lux_price_history(timeframe="1hr", token_id="lux-token"):
    """Get price history with specified timeframe."""
    try:
        logger.info(f"Fetching live price data for {token_id} with timeframe {timeframe}")
        timestamps, prices, _ = await fetch_market_data(token_id, timeframe)  # Updated function call

        if timestamps and prices:
            logger.info(f"Successfully retrieved {len(prices)} price points")
            logger.info(f"Latest price: ${prices[-1]:.6f}")
            return timestamps, prices

        logger.warning("Failed to fetch price data")
        return None, None
    except Exception as e:
        logger.error(f"Error in price history retrieval: {str(e)}")
        return None, None

async def create_price_chart(timeframe="1hr", token_id="lux-token", token_symbol="LUX", entry_price=None):
    """Create a simple line chart showing price movement."""
    try:
        # Get price data
        logger.info(f"Starting price chart generation for {token_symbol} with timeframe {timeframe}")
        timestamps, prices = await get_lux_price_history(timeframe, token_id)
        if not timestamps or not prices:
            logger.error("Failed to get price data")
            return None, None, None

        # Chart dimensions and setup
        width = 1280
        height = 720
        padding = 80
        top_padding = 100
        bottom_padding = 100

        # Create image with dark theme
        img = Image.new('RGB', (width, height), '#0A2A12')  # Dark green background
        draw = ImageDraw.Draw(img)

        # Calculate chart dimensions
        chart_width = width - (2 * padding)
        chart_height = height - (top_padding + bottom_padding)

        # Calculate price range
        if entry_price is not None:
            max_price = max(max(prices), entry_price) * 1.05  # Add 5% padding
            min_price = min(min(prices), entry_price) * 0.95  # Add 5% padding
        else:
            max_price = max(prices) * 1.05  # Add 5% padding
            min_price = min(prices) * 0.95  # Add 5% padding

        price_range = max_price - min_price

        # Load fonts
        try:
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            price_font = time_font
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            crash_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            time_font = price_font = title_font = crash_font = ImageFont.load_default()

        # Colors
        grid_color = '#0D3517'  # Slightly lighter green for grid
        label_color = '#FFFFFF'
        line_color = '#FF3333'

        # Calculate crash percentage if entry price is provided
        if entry_price is not None:
            crash_percent = ((entry_price - prices[-1]) / entry_price) * 100
        else:
            crash_percent = None

        # Title text settings with background outline for better visibility
        title = f"${token_symbol} {timeframe} Chart"
        title_width = draw.textlength(title, font=title_font)
        title_x = (img.width - title_width) / 2
        title_y = 30

        # Draw title with outline
        outline_color = '#000000'
        outline_width = 2
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((title_x + dx, title_y + dy), title, font=title_font, fill=outline_color)

        # Draw main title text
        draw.text((title_x, title_y), title, font=title_font, fill='#FFFFFF')

        # Add crash percentage text under title if applicable
        if crash_percent is not None:
            crash_text = f"Down {crash_percent:.1f}% Since NWA Takeover"
            crash_width = draw.textlength(crash_text, font=crash_font)
            crash_x = (img.width - crash_width) / 2
            crash_y = title_y + 60

            # Draw crash text with outline
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((crash_x + dx, crash_y + dy), crash_text, font=crash_font, fill=outline_color)

            # Draw main crash text in red
            draw.text((crash_x, crash_y), crash_text, font=crash_font, fill='#FF0000')

        # Draw horizontal grid lines and price labels
        for i in range(6):
            price = min_price + (i * (price_range / 5))
            y = top_padding + ((max_price - price) * chart_height / price_range)
            draw.line([(padding, y), (width - padding, y)], fill=grid_color, width=1)
            price_str = format_price_label(price)
            draw.text((10, y - 16), price_str, fill=label_color, font=price_font)

        # Draw entry price line if provided
        if entry_price is not None:
            entry_y = top_padding + ((max_price - entry_price) * chart_height / price_range)
            # Draw dashed line using small segments
            dash_length = 10
            x_start = padding
            x_end = width - padding

            # Draw blue dashed line
            for x in range(int(x_start), int(x_end), dash_length * 2):
                draw.line([(x, entry_y), (x + dash_length, entry_y)], 
                         fill='#0000FF', width=2)

            # Add label for entry price line in white
            label = "NWA Takeover"
            label_width = draw.textlength(label, font=time_font)
            draw.text((x_start + 10, entry_y - 20), label, 
                     font=time_font, fill='#FFFFFF')

        # Draw time labels and vertical grid lines
        for i in range(8):
            x = padding + (i * chart_width / 7)
            index = int((i / 7) * (len(timestamps) - 1))
            timestamp = timestamps[index]

            draw.line([(x, top_padding), (x, height - bottom_padding)], fill=grid_color)
            time_str, date_str = format_time_label(timestamp, timeframe)

            # Center and draw time labels
            time_width = draw.textlength(time_str, font=time_font)
            date_width = draw.textlength(date_str, font=time_font)

            if time_str:
                draw.text((x - time_width/2, height - bottom_padding + 10), 
                         time_str, fill=label_color, font=time_font)

            draw.text((x - date_width/2, height - bottom_padding + 30), 
                     date_str, fill=label_color, font=time_font)

        # Draw price line
        points = []
        for timestamp, price in zip(timestamps, prices):
            x = padding + ((timestamp - timestamps[0]) * chart_width / (timestamps[-1] - timestamps[0]))
            y = top_padding + ((max_price - price) * chart_height / price_range)
            points.append((x, y))

        if len(points) > 1:
            draw.line(points, fill='#FF6666', width=5)  # Background glow
            draw.line(points, fill=line_color, width=3)  # Main line

        # Save chart
        chart_path = f"price_chart_{int(datetime.now().timestamp())}.png"
        img.save(chart_path, quality=95)
        logger.info(f"Successfully saved chart: {chart_path}")

        return chart_path, timestamps, prices

    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None