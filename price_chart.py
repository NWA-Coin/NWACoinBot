import os
import logging
from datetime import datetime
import pytz
from PIL import Image, ImageDraw, ImageFont
from market_data import fetch_lux_market_data

# Set up logging
logger = logging.getLogger('discord_bot')

# Define Eastern timezone
eastern = pytz.timezone('US/Eastern')

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

def format_price_label(price):
    """Format price in cents."""
    cents = price * 100
    return f"{cents:.1f}¢"

def format_time_label(timestamp):
    """Simple time label format."""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, pytz.UTC)
        eastern_time = dt.astimezone(eastern)
        return eastern_time.strftime("%H:%M")
    except Exception as e:
        logger.error(f"Error formatting time label: {str(e)}")
        return "N/A"

async def create_price_chart(timeframe="1hr"):
    """Create a simple line chart showing price movement."""
    try:
        # Get price data
        logger.info(f"Starting price chart generation for timeframe {timeframe}")
        timestamps, prices = await get_lux_price_history(timeframe)
        if not timestamps or not prices:
            logger.error("Failed to get price data")
            return None

        # Chart dimensions
        width = 1280
        height = 720
        padding = 70  # Increased padding for better label spacing

        # Create image with dark theme
        img = Image.new('RGB', (width, height), '#1E2124')
        draw = ImageDraw.Draw(img)

        # Calculate chart dimensions
        chart_width = width - (2 * padding)
        chart_height = height - (2 * padding)

        # Calculate price range with padding
        max_price = max(prices) * 1.02  # Add 2% padding
        min_price = min(prices) * 0.98  # Add 2% padding
        price_range = max_price - min_price

        # Load font with increased size for better readability
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            logger.info("Loaded custom font successfully")
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            font = ImageFont.load_default()

        # Draw grid and labels
        grid_color = '#2F3136'
        label_color = '#FFFFFF'
        line_color = '#FF4444'  # Red line for price dumps

        # Draw horizontal grid lines and price labels
        for i in range(6):
            price = min_price + (i * (price_range / 5))
            y = padding + ((max_price - price) * chart_height / price_range)

            # Grid line
            draw.line([(padding, y), (width - padding, y)], fill=grid_color, width=1)

            # Price label
            price_str = format_price_label(price)
            draw.text((10, y - 12), price_str, fill=label_color, font=font)

        # Draw time labels and vertical grid lines
        num_labels = 6
        for i in range(num_labels):
            x = padding + (i * chart_width / (num_labels - 1))
            timestamp = timestamps[0] + (i * (timestamps[-1] - timestamps[0]) / (num_labels - 1))

            # Grid line
            draw.line([(x, padding), (x, height - padding)], fill=grid_color)

            # Time label
            time_str = format_time_label(timestamp)
            draw.text((x - 20, height - padding + 10), time_str, fill=label_color, font=font)

        # Draw price line with increased thickness
        points = []
        for timestamp, price in zip(timestamps, prices):
            x = padding + ((timestamp - timestamps[0]) * chart_width / (timestamps[-1] - timestamps[0]))
            y = padding + ((max_price - price) * chart_height / price_range)
            points.append((x, y))

        if len(points) > 1:
            draw.line(points, fill=line_color, width=3)  # Increased line width

        # Save chart with high quality
        chart_path = f"price_chart_{int(datetime.now().timestamp())}.png"
        img.save(chart_path, quality=95)
        logger.info(f"Successfully saved chart: {chart_path}")
        return chart_path

    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.exception("Full traceback:")
        return None