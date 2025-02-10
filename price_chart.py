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
    return f"{cents:.2f}¢"  # Keeping the 2 decimal points

def format_time_label(timestamp, timeframe="1hr"):
    """Format time label with standardized intervals and dates."""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000, pytz.UTC)
        eastern_time = dt.astimezone(eastern)

        # Format with date for all timestamps
        return eastern_time.strftime("%-m/%-d\n%-I:%M %p")
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

        # Ensure data ends at current time
        current_time = int(datetime.now().timestamp() * 1000)
        if timestamps[-1] < current_time:
            timestamps.append(current_time)
            prices.append(prices[-1])  # Use last known price

        # Log price data for debugging
        logger.info(f"Price data points: {len(prices)}")
        logger.info(f"First price: ${prices[0]:.6f}, Last price: ${prices[-1]:.6f}")

        # Chart dimensions
        width = 1280
        height = 720
        padding = 80  # Base padding
        top_padding = 100  # Extra padding for top text
        bottom_padding = 100  # Extra padding for bottom text

        # Create image with dark theme
        img = Image.new('RGB', (width, height), '#1E2124')
        draw = ImageDraw.Draw(img)

        # Calculate chart dimensions
        chart_width = width - (2 * padding)
        chart_height = height - (top_padding + bottom_padding)  # Adjusted height for extra padding

        # Calculate price range with padding
        max_price = max(prices) * 1.02  # Add 2% padding
        min_price = min(prices) * 0.98  # Add 2% padding
        price_range = max_price - min_price

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        except Exception as e:
            logger.warning(f"Failed to load custom font: {str(e)}. Using default.")
            font = ImageFont.load_default()

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
            draw.text((10, y - 16), price_str, fill=label_color, font=font)

        # Determine number of time labels based on timeframe
        if timeframe == "5m":
            num_labels = 12  # Every 30 minutes
        elif timeframe == "15m":
            num_labels = 8   # Hourly
        else:  # 1hr
            num_labels = 6   # Every 4 hours

        # Draw time labels and vertical grid lines
        time_interval = (timestamps[-1] - timestamps[0]) / (num_labels - 1)
        for i in range(num_labels):
            x = padding + (i * chart_width / (num_labels - 1))
            timestamp = timestamps[0] + (i * time_interval)
            draw.line([(x, top_padding), (x, height - bottom_padding)], fill=grid_color)
            time_str = format_time_label(timestamp, timeframe)
            draw.text((x - 25, height - bottom_padding + 20), time_str, fill=label_color, font=font)

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