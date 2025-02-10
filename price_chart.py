import os
import logging
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont
from market_data import fetch_lux_market_data
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

        # Include both date and time for all timeframes
        if timeframe in ["5m", "15m", "1hr"]:
            time_str = eastern_time.strftime("%-I:%M %p")
            date_str = eastern_time.strftime("%m/%d")
        elif timeframe == "24hr":
            time_str = eastern_time.strftime("%-I%p")
            date_str = eastern_time.strftime("%m/%d")
        elif timeframe == "7d":
            time_str = eastern_time.strftime("%a")
            date_str = eastern_time.strftime("%m/%d")
        elif timeframe in ["1m", "3m"]:
            time_str = eastern_time.strftime("")
            date_str = eastern_time.strftime("%m/%d")

        return time_str, date_str
    except Exception as e:
        logger.error(f"Error formatting time label: {str(e)}")
        return "N/A", "N/A"

async def get_lux_price_history(timeframe="1hr"):
    """Get LUX price history with specified timeframe."""
    try:
        logger.info(f"Fetching live LUX price data for timeframe {timeframe}")
        timestamps, prices, _ = await fetch_lux_market_data(timeframe)

        if timestamps and prices:
            logger.info(f"Successfully retrieved {len(prices)} price points")
            logger.info(f"Latest price: ${prices[-1]:.6f}")
            return timestamps, prices

        logger.warning("Failed to fetch price data")
        return None, None
    except Exception as e:
        logger.error(f"Error in price history retrieval: {str(e)}")
        return None, None

async def create_price_chart(timeframe="1hr"):
    """Create a simple line chart showing price movement."""
    try:
        # Get price data
        logger.info(f"Starting price chart generation for timeframe {timeframe}")
        timestamps, prices = await get_lux_price_history(timeframe)
        if not timestamps or not prices:
            logger.error("Failed to get price data")
            return None, None, None

        # Log price data for debugging
        logger.info(f"Price data points: {len(prices)}")
        logger.info(f"First price: ${prices[0]:.6f}, Last price: ${prices[-1]:.6f}")

        # Chart dimensions
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

        # Calculate price range with padding
        max_price = max(prices) * 1.05  # Add 5% padding
        min_price = min(prices) * 0.95  # Add 5% padding
        price_range = max_price - min_price

        try:
            # Load fonts with consistent size for all labels
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)  # Reduced size
            price_font = time_font  # Use same font for price labels
            # Military-style font for header
            header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 24)  # Smaller header
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            time_font = price_font = header_font = ImageFont.load_default()

        # Draw grid and labels with adjusted colors
        grid_color = '#0D3517'  # Slightly lighter green for grid
        label_color = '#FFFFFF'
        line_color = '#FF3333'

        # Create title based on timeframe
        title = f"$LUX {timeframe} Chart"

        # Center the title
        title_width = draw.textlength(title, font=header_font)
        title_x = (width - title_width) / 2
        title_y = 20  # Adjust vertical position as needed

        # Draw outline and text for centered title
        outline_color = 'black'
        outline_width = 2

        # Draw outline
        for dx in range(-outline_width, outline_width+1):
            for dy in range(-outline_width, outline_width+1):
                if dx != 0 or dy != 0:
                    draw.text((title_x+dx, title_y+dy), title, font=header_font, fill=outline_color)

        # Draw main title text
        draw.text((title_x, title_y), title, font=header_font, fill=label_color)

        # Draw horizontal grid lines and price labels
        for i in range(6):
            price = min_price + (i * (price_range / 5))
            y = top_padding + ((max_price - price) * chart_height / price_range)
            draw.line([(padding, y), (width - padding, y)], fill=grid_color, width=1)
            price_str = format_price_label(price)
            draw.text((10, y - 16), price_str, fill=label_color, font=price_font)

        # Calculate nice intervals for time labels
        if timeframe in ["5m", "15m"]:
            num_labels = 6
        elif timeframe == "1hr":
            num_labels = 7
        elif timeframe == "24hr":
            num_labels = 8
        elif timeframe == "7d":
            num_labels = 7  # One for each day
        else:
            num_labels = 8

        # Draw time labels and vertical grid lines with two-line format
        for i in range(num_labels):
            x = padding + (i * chart_width / (num_labels - 1))
            index = int((i / (num_labels - 1)) * (len(timestamps) - 1))
            timestamp = timestamps[index]

            draw.line([(x, top_padding), (x, height - bottom_padding)], fill=grid_color)
            time_str, date_str = format_time_label(timestamp, timeframe)

            # Calculate text widths for centering
            time_width = draw.textlength(time_str, font=time_font)
            date_width = draw.textlength(date_str, font=time_font)

            # Draw time on top line
            if time_str:  # Only draw if time string is not empty
                draw.text((x - time_width/2, height - bottom_padding + 10), 
                         time_str, fill=label_color, font=time_font)

            # Draw date on bottom line
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