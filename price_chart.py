import os
import logging
from datetime import datetime, timedelta
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pytz
import math
from market_data import fetch_lux_market_data

# Set up logging
logger = logging.getLogger('discord_bot')

# Define Eastern timezone
eastern = pytz.timezone('US/Eastern')

# Add NWA entry price as a configurable constant
NWA_ENTRY_PRICE = 0.015  # 1.5 cents entry price

async def get_lux_price_history(timeframe="1hr"):
    """Get LUX price history with specified timeframe."""
    try:
        logger.info(f"Fetching live LUX price data for timeframe {timeframe}")

        # Try to fetch live market data first
        timestamps, prices, candles = await fetch_lux_market_data(timeframe)

        if timestamps and prices and candles:
            logger.info(f"Successfully retrieved {len(prices)} price points")
            logger.info(f"Latest price: ${prices[-1]:.6f}")
            logger.info(f"First timestamp: {datetime.fromtimestamp(timestamps[0]/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Last timestamp: {datetime.fromtimestamp(timestamps[-1]/1000).strftime('%Y-%m-%d %H:%M:%S')}")

            if await validate_price_data(timestamps, prices, candles):
                return timestamps, prices, candles
            else:
                logger.error("Live market data validation failed. Falling back to simulation.")
                return await generate_simulated_price_history(timeframe)
        else:
            # Fall back to simulated data if live data fails
            logger.warning("Failed to fetch live data, falling back to simulation")
            return await generate_simulated_price_history(timeframe)

    except Exception as e:
        logger.error(f"Error in price history retrieval: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None

async def generate_simulated_price_history(timeframe="1hr"):
    """Generate simulated price history as fallback."""
    try:
        logger.info(f"Generating simulated price data for timeframe {timeframe}")

        # Set consistent seeds for reproducibility
        seed = int(datetime.now().timestamp()) // 300
        np.random.seed(seed)
        logger.info(f"Using seed {seed} for random generation")

        # Configure timeframes
        timeframe_config = {
            "5m": {
                "periods": 144,    # 12 hours in 5-minute intervals
                "start_price": 0.0048,
                "current_price": 0.0037,
                "volatility": 0.003,
                "interval": 300    # 5 minutes in seconds
            },
            "15m": {
                "periods": 96,     # 24 hours in 15-minute intervals
                "start_price": 0.0052,
                "current_price": 0.0037,
                "volatility": 0.004,
                "interval": 900    # 15 minutes in seconds
            },
            "1hr": {
                "periods": 72,     # 3 days in 1-hour intervals
                "start_price": 0.0048,
                "current_price": 0.0037,
                "volatility": 0.005,
                "interval": 3600   # 1 hour in seconds
            }
        }

        config = timeframe_config.get(timeframe, timeframe_config["1hr"])
        logger.info(f"Using configuration for {timeframe} timeframe: {config}")

        # Generate timestamps with proper rounding to intervals
        end_time = datetime.now(eastern)
        interval_seconds = config["interval"]
        interval_minutes = interval_seconds // 60
        current_minutes = end_time.minute
        rounded_minutes = ((current_minutes + interval_minutes - 1) // interval_minutes) * interval_minutes
        if rounded_minutes >= 60:
            end_time = end_time.replace(hour=end_time.hour + 1, minute=0, second=0, microsecond=0)
        else:
            end_time = end_time.replace(minute=rounded_minutes, second=0, microsecond=0)
        logger.info(f"End time (Eastern): {end_time}, rounded_minutes: {rounded_minutes}")

        timestamps = []
        prices = []
        candles = []

        # Calculate start time and ensure it's properly rounded
        total_duration = config["periods"] * config["interval"]
        start_time = end_time - timedelta(seconds=total_duration)
        start_time = start_time.replace(second=0, microsecond=0)

        # Round start time to proper interval
        start_minutes = (start_time.minute // interval_minutes) * interval_minutes
        start_time = start_time.replace(minute=start_minutes)
        logger.info(f"Start time (Eastern): {start_time}, start_minutes: {start_minutes}")

        # Initialize price variables with improved parameters
        current_price = config["start_price"]
        trend = -1  # Start with consistent downward trend
        trend_strength = np.random.uniform(0.4, 0.8)  # Increased strength range
        volatility_base = config["volatility"]
        momentum = 0

        logger.info(f"Initial conditions: trend={trend}, trend_strength={trend_strength:.3f}, volatility={volatility_base:.6f}")

        # Target price calculation
        target_price = config["current_price"]
        price_distance = target_price - current_price
        periods_remaining = config["periods"]

        for i in range(config["periods"]):
            current_time = start_time + timedelta(seconds=i * config["interval"])
            timestamp = int(current_time.timestamp() * 1000)

            # Log candle generation progress
            if i % 10 == 0:  # Log every 10th candle
                logger.info(f"Generating candle {i}/{config['periods']}: time={current_time.strftime('%m/%d %H:%M')}, price={current_price:.6f}")

            # Adjust trend strength based on progress to target
            if periods_remaining > 0:
                target_change = price_distance / periods_remaining
                trend_strength = abs(target_change / current_price) * 1.5

            # Generate price movement with improved realism
            trend_effect = trend * trend_strength * volatility_base
            random_walk = np.random.normal(0, volatility_base * 0.5)
            target_effect = 0.15 * (target_price - current_price) / current_price

            # Time-based volatility scaling
            hour = current_time.hour
            volatility_scale = 1.2 if 9 <= hour <= 16 else 0.8

            price_change = (trend_effect + random_walk + target_effect + momentum) * volatility_scale
            current_price *= (1 + price_change)
            momentum = 0.7 * momentum + 0.3 * price_change * trend_strength

            # Ensure price stays within realistic bounds
            current_price = max(min(current_price, config["start_price"] * 1.2),
                                 target_price * 0.8)

            timestamps.append(timestamp)
            prices.append(current_price)

            # Generate candle data with more realistic ranges
            volatility_factor = np.random.uniform(0.5, 2.0) * volatility_base
            range_factor = 1 + abs(momentum)

            if trend > 0:
                high = current_price * (1 + volatility_factor * range_factor)
                low = current_price * (1 - volatility_factor * 0.7)
            else:
                high = current_price * (1 + volatility_factor * 0.7)
                low = current_price * (1 - volatility_factor * range_factor)

            # Ensure open price connects with previous close
            open_price = prices[-2] if i > 0 else current_price

            candle = {
                'timestamp': timestamp,
                'open': open_price,
                'high': max(high, open_price, current_price),
                'low': min(low, open_price, current_price),
                'close': current_price
            }
            candles.append(candle)

            periods_remaining -= 1

            # Log significant price movements
            if abs(price_change) > 0.02:  # Log large price changes
                logger.info(f"Large price movement at {current_time}: {price_change:.2%}")

        logger.info(f"Generated {len(candles)} candles from {start_time} to {end_time}")
        logger.info(f"Final price: {current_price:.6f}")
        return timestamps, prices, candles

    except Exception as e:
        logger.error(f"Error in price history generation: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None


def get_nice_scale_interval(min_val, max_val):
    """Calculate a nice scale interval for the Y-axis."""
    range_in_cents = (max_val - min_val) * 100
    logger.info(f"Price range in cents: {range_in_cents:.4f}")

    # Define standard intervals in cents (0.1¢ increments)
    standard_intervals = [
        0.1,    # 0.1 cents
        0.2,    # 0.2 cents
        0.3,    # 0.3 cents
        0.4,    # 0.4 cents
        0.5,    # 0.5 cents
        1.0,    # 1.0 cents
        2.0,    # 2.0 cents
        5.0     # 5.0 cents
    ]

    # Target around 5-7 intervals on the axis
    target_divisions = 6
    raw_interval = range_in_cents / target_divisions
    logger.info(f"Raw interval: {raw_interval:.4f} cents")

    # Find the closest standard interval that gives nice divisions
    selected_interval = standard_intervals[-1]  # Default to largest
    for interval in standard_intervals:
        num_divisions = range_in_cents / interval
        if num_divisions >= 4 and num_divisions <= 8:  # Aim for 4-8 divisions
            selected_interval = interval
            break
        if interval > raw_interval:
            selected_interval = interval
            break

    logger.info(f"Selected interval: {selected_interval:.1f} cents")
    return selected_interval / 100  # Convert back to decimal

def format_price_label(price):
    """Format price in cents with consistent decimal places."""
    cents = price * 100  # Convert to cents

    # Always show prices with one decimal place for consistency
    formatted = f"{cents:.1f}¢"
    logger.info(f"Formatted price {price} as {formatted}")
    return formatted

async def validate_price_data(timestamps, prices, candles):
    """Validate price data for consistency and accuracy."""
    if not all([timestamps, prices, candles]):
        logger.error("Missing required price data components")
        return False

    try:
        # Validate basic data structure
        if len(timestamps) != len(prices) or len(timestamps) != len(candles):
            logger.error("Mismatched data lengths")
            return False

        # Validate price ranges
        for i, candle in enumerate(candles):
            if not (0 < candle['low'] <= candle['high'] < 1):  # Assuming price should be between 0 and 1 USD
                logger.warning(f"Invalid price range in candle {i}: low={candle['low']}, high={candle['high']}")
                return False

            # Verify OHLC relationships
            if not (candle['low'] <= candle['open'] <= candle['high'] and 
                   candle['low'] <= candle['close'] <= candle['high']):
                logger.warning(f"Invalid OHLC relationships in candle {i}")
                return False

        logger.info("Price data validation passed")
        return True

    except Exception as e:
        logger.error(f"Error validating price data: {str(e)}")
        return False

def draw_dashed_line(draw, start, end, color, width=1, dash_length=10):
    """Draw a dashed line since PIL doesn't support the dash parameter."""
    x1, y1 = start
    x2, y2 = end

    # Calculate line length and angle
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    if length == 0:
        return

    # Calculate dx and dy for each dash
    dx = (x2 - x1) * dash_length / length
    dy = (y2 - y1) * dash_length / length

    # Draw dashes
    curr_x, curr_y = x1, y1
    is_dash = True  # Start with a dash

    while ((curr_x - x1) * (x2 - x1) + (curr_y - y1) * (y2 - y1)) < length * length:
        next_x = min(curr_x + dx, x2) if x2 > x1 else max(curr_x + dx, x2)
        next_y = min(curr_y + dy, y2) if y2 > y1 else max(curr_y + dy, y2)

        if is_dash:
            draw.line([(curr_x, curr_y), (next_x, next_y)], fill=color, width=width)

        curr_x, curr_y = next_x, next_y
        is_dash = not is_dash

async def create_price_chart(timeframe="1hr", use_nwa_price=False):
    """Create a traditional candlestick chart with clear visuals."""
    try:
        # Get price data
        timestamps, prices, candles = await get_lux_price_history(timeframe)

        # Validate price data
        if not await validate_price_data(timestamps, prices, candles):
            logger.error("Price data validation failed")
            return None

        # Chart dimensions and padding
        width = 1280
        height = 720
        padding = 60

        # Create image with dark theme
        img = Image.new('RGB', (width, height), '#1E2124')
        draw = ImageDraw.Draw(img)

        # Calculate chart dimensions
        chart_width = width - (2 * padding)
        chart_height = height - (2 * padding)

        # Calculate price range with padding
        high_prices = [c['high'] for c in candles]
        low_prices = [c['low'] for c in candles]

        # Only include NWA price in range calculation if specifically requested
        if use_nwa_price:
            high_prices.append(NWA_ENTRY_PRICE)
            low_prices.append(NWA_ENTRY_PRICE * 0.8)  # Show some range below entry

        max_price = max(high_prices) * 1.02
        min_price = min(low_prices) * 0.98
        price_range = max_price - min_price

        # Get a nice interval for the scale
        interval = get_nice_scale_interval(min_price, max_price)

        # Load fonts
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except Exception as e:
            logger.warning(f"Font loading failed: {str(e)}. Using default font.")
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw grid and labels
        grid_color = '#2F3136'
        label_color = '#FFFFFF'

        # Draw horizontal grid lines and price labels
        num_intervals = int((max_price - min_price) / interval)
        for i in range(num_intervals + 1):
            price = min_price + (i * interval)
            y = padding + ((max_price - price) * chart_height / price_range)

            # Only draw if within chart bounds
            if padding <= y <= height - padding:
                draw.line([(padding, y), (width - padding, y)], fill=grid_color, width=1)
                price_str = format_price_label(price)
                text_bbox = draw.textbbox((0, 0), price_str, font=small_font)
                text_width = text_bbox[2] - text_bbox[0]
                draw.text((padding - text_width - 5, y - 10), price_str, fill=label_color, font=small_font)

        # Draw vertical grid lines and time labels
        num_vert_lines = 8
        for i in range(num_vert_lines + 1):
            x = padding + (i * chart_width // num_vert_lines)
            draw.line([(x, padding), (x, height - padding)], fill=grid_color, width=1)

            if i < len(candles):
                idx = int((i * (len(candles) - 1)) / num_vert_lines)
                if idx < len(candles):
                    utc_dt = datetime.fromtimestamp(candles[idx]['timestamp'] / 1000, pytz.UTC)
                    eastern_dt = utc_dt.astimezone(eastern)
                    time_str = eastern_dt.strftime("%m/%d\n%H:%M")
                    text_width = len(time_str) * 5
                    draw.text((x - text_width / 2, height - padding + 10),
                             time_str, fill=label_color, font=small_font)

        # Draw candlesticks with improved visibility
        candle_spacing = chart_width / len(candles)
        candle_width = max(3, min(candle_spacing * 0.8, 8))

        for i, candle in enumerate(candles):
            x = padding + (i * candle_spacing)

            # Calculate y-coordinates using the price range
            open_y = padding + ((max_price - candle['open']) * chart_height / price_range)
            close_y = padding + ((max_price - candle['close']) * chart_height / price_range)
            high_y = padding + ((max_price - candle['high']) * chart_height / price_range)
            low_y = padding + ((max_price - candle['low']) * chart_height / price_range)

            # Determine candle color (red for down, green for up)
            color = '#FF4444' if candle['close'] < candle['open'] else '#44FF44'

            # Draw wick
            wick_x = x + (candle_width / 2)
            draw.line([(wick_x, high_y), (wick_x, low_y)], fill=color, width=1)

            # Draw candle body
            draw.rectangle([
                x, min(open_y, close_y),
                x + candle_width, max(open_y, close_y)
            ], fill=color, outline=color)

        # Draw NWA entry price line only if specifically requested
        if use_nwa_price:
            entry_y = padding + ((max_price - NWA_ENTRY_PRICE) * chart_height / price_range)
            # Use custom dashed line function instead of unsupported dash parameter
            draw_dashed_line(
                draw, 
                (padding, entry_y), 
                (width - padding, entry_y),
                color='#FF4444',
                width=2,
                dash_length=10
            )
            price_str = "NWA Entry: 1.50¢"
            draw.text((padding + 10, entry_y - 20), price_str, 
                     fill='#FF4444', font=small_font)

        # Save chart
        try:
            chart_path = f"price_chart_{int(datetime.now().timestamp())}.png"
            img.save(chart_path, quality=95)
            logger.info(f"Successfully saved chart: {chart_path}")
            return chart_path
        except Exception as e:
            logger.error(f"Failed to save chart: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.exception("Full traceback:")
        return None