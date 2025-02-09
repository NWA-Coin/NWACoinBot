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
            return timestamps, prices, _  # Return all values to maintain consistency

        logger.warning("Failed to fetch price data")
        return None, None, None
    except Exception as e:
        logger.error(f"Error in price history retrieval: {str(e)}")
        return None, None, None

def format_price_label(price):
    """Format price in cents with consistent decimal places."""
    cents = price * 100
    return f"{cents:.1f}¢"

def format_time_label(timestamp, timeframe):
    """Format time label based on timeframe with consistent spacing."""
    try:
        utc_dt = datetime.fromtimestamp(timestamp / 1000, pytz.UTC)
        eastern_dt = utc_dt.astimezone(eastern)
        logger.info(f"Formatting time label for timestamp {timestamp} in {timeframe} timeframe")

        if timeframe == "5m":
            # For 5m, show HH:MM with consistent spacing
            return eastern_dt.strftime("%H:%M")
        elif timeframe == "15m":
            # For 15m, show HH:MM with consistent spacing
            return eastern_dt.strftime("%H:%M")
        else:  # 1hr
            # For hourly view, show MM/DD HH:MM if spanning multiple days
            curr_day = datetime.now(eastern).strftime("%d")
            if eastern_dt.strftime("%d") != curr_day:
                return eastern_dt.strftime("%m/%d\n%H:%M")
            return eastern_dt.strftime("%H:%M")
    except Exception as e:
        logger.error(f"Error formatting time label: {str(e)}")
        return "N/A"  # Fallback label

async def create_price_chart(timeframe="1hr"):
    """Create a simple line chart showing price movement."""
    try:
        # Get price data
        logger.info(f"Starting price chart generation for timeframe {timeframe}")
        timestamps, prices, _ = await fetch_lux_market_data(timeframe)
        if not timestamps or not prices:
            logger.error("Failed to get price data")
            return None

        # Chart dimensions and padding
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
        max_price = max(prices) * 1.02
        min_price = min(prices) * 0.98
        price_range = max_price - min_price

        # Load font with increased size
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

        # Draw horizontal grid lines and price labels with consistent spacing
        num_price_lines = 6
        for i in range(num_price_lines):
            price = min_price + (i * (price_range / (num_price_lines - 1)))
            y = height - padding - ((price - min_price) * chart_height / price_range)

            # Draw grid line
            draw.line([(padding, y), (width - padding, y)], fill=grid_color, width=1)

            # Draw price label
            price_str = format_price_label(price)
            label_width = draw.textlength(price_str, font=font)
            draw.text((padding - label_width - 10, y - 16), price_str, fill=label_color, font=font)

        # Draw time labels and vertical grid lines with consistent spacing
        time_interval = (timestamps[-1] - timestamps[0]) / 5  # Divide into 5 segments
        for i in range(6):  # 6 points for 5 segments
            x_pos = padding + (i * chart_width / 5)
            timestamp = timestamps[0] + (i * time_interval)

            # Draw vertical grid line
            draw.line([(x_pos, padding), (x_pos, height - padding)], fill=grid_color, width=1)

            # Format and draw time label
            time_str = format_time_label(int(timestamp), timeframe)
            label_width = draw.textlength(time_str, font=font)
            draw.text((x_pos - label_width/2, height - padding + 10), 
                     time_str, fill=label_color, font=font)

        # Draw price line with increased thickness
        points = []
        for timestamp, price in zip(timestamps, prices):
            x = padding + ((timestamp - timestamps[0]) * chart_width / (timestamps[-1] - timestamps[0]))
            y = height - padding - ((price - min_price) * chart_height / price_range)
            points.append((x, y))

        if len(points) > 1:
            draw.line(points, fill=line_color, width=3)

        # Save chart with unique timestamp
        chart_path = f"price_chart_{int(datetime.now().timestamp())}.png"

        try:
            img.save(chart_path, quality=95)
            logger.info(f"Successfully saved chart: {chart_path}")

            # Verify file was created successfully
            if os.path.exists(chart_path) and os.path.getsize(chart_path) > 0:
                return chart_path
            else:
                logger.error("Chart file was not created successfully")
                return None

        except Exception as e:
            logger.error(f"Error saving chart file: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.exception("Full traceback:")
        return None