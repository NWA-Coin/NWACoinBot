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
    return f"{cents:.2f}¢"

def format_time_label(timestamp):
    """Format time label."""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, pytz.UTC)
        eastern_time = dt.astimezone(eastern)
        return eastern_time.strftime("%-I:%M %p")
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
        img = Image.new('RGB', (width, height), '#1E2124')
        draw = ImageDraw.Draw(img)

        # Calculate chart dimensions
        chart_width = width - (2 * padding)
        chart_height = height - (top_padding + bottom_padding)

        # Calculate price range with padding
        max_price = max(prices) * 1.02  # Add 2% padding
        min_price = min(prices) * 0.98  # Add 2% padding
        price_range = max_price - min_price

        try:
            # Load fonts
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            time_font = price_font = ImageFont.load_default()

        # Draw grid and labels
        grid_color = '#2F3136'
        label_color = '#FFFFFF'
        line_color = '#FF3333'

        # Draw horizontal grid lines and price labels
        for i in range(6):
            price = min_price + (i * (price_range / 5))
            y = top_padding + ((max_price - price) * chart_height / price_range)
            draw.line([(padding, y), (width - padding, y)], fill=grid_color, width=1)
            price_str = format_price_label(price)
            draw.text((10, y - 16), price_str, fill=label_color, font=price_font)

        # Draw time labels and vertical grid lines
        num_labels = 8  # Fixed number of labels
        for i in range(num_labels):
            x = padding + (i * chart_width / (num_labels - 1))
            index = int((i / (num_labels - 1)) * (len(timestamps) - 1))
            timestamp = timestamps[index]

            draw.line([(x, top_padding), (x, height - bottom_padding)], fill=grid_color)
            time_str = format_time_label(timestamp)
            # Center the time label under the grid line
            time_width = draw.textlength(time_str, font=time_font)
            draw.text((x - time_width/2, height - bottom_padding + 20), time_str, fill=label_color, font=time_font)

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