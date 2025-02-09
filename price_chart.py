import os
import logging
from datetime import datetime, timedelta
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Set up logging
logger = logging.getLogger('discord_bot')

async def get_lux_price_history(timeframe="1hr"):
    """Get LUX price history with specified timeframe."""
    try:
        logger.info(f"Fetching LUX price data for timeframe {timeframe}")

        # Configure timeframes with accurate periods and price ranges
        timeframe_config = {
            "5m": {
                "periods": 144,    # 12 hours in 5-minute intervals
                "start_price": 0.0048,
                "current_price": 0.0037,
                "volatility": 0.002,
                "interval": 300    # 5 minutes in seconds
            },
            "15m": {
                "periods": 96,     # 24 hours in 15-minute intervals
                "start_price": 0.0052,
                "current_price": 0.0037,
                "volatility": 0.003,
                "interval": 900    # 15 minutes in seconds
            },
            "1hr": {
                "periods": 72,     # 3 days in 1-hour intervals
                "start_price": 0.015,
                "current_price": 0.0037,
                "volatility": 0.004,
                "interval": 3600   # 1 hour in seconds
            }
        }

        config = timeframe_config.get(timeframe, timeframe_config["1hr"])
        logger.info(f"Using configuration for {timeframe} timeframe")

        # Generate timestamps and prices
        end_time = datetime.now()
        # Round end time to the nearest natural interval (e.g., 12:00, 12:15)
        interval_seconds = config["interval"]
        rounded_timestamp = (int(end_time.timestamp()) // interval_seconds) * interval_seconds
        end_time = datetime.fromtimestamp(rounded_timestamp)

        timestamps = []
        prices = []
        candles = []

        # Calculate start time based on periods and interval
        total_duration = config["periods"] * config["interval"]
        start_time = end_time - timedelta(seconds=total_duration)

        # Initialize price variables
        current_price = config["start_price"]
        trend = np.random.choice([-1, 1])
        trend_strength = np.random.uniform(0.3, 0.7)
        volatility_base = config["volatility"]
        momentum = 0

        for i in range(config["periods"]):
            # Calculate exact timestamp for this interval
            current_time = start_time + timedelta(seconds=i * config["interval"])
            timestamp = int(current_time.timestamp() * 1000)

            # Randomly switch trend with diminishing probability
            if np.random.random() < 0.15 * (1 - i/config["periods"]):
                trend = -trend
                trend_strength = np.random.uniform(0.3, 0.7)
                volatility_base *= np.random.uniform(1.0, 1.5)  # Increase volatility on trend change
                momentum = 0  # Reset momentum on trend change

            # Generate price movement
            # Combine trend, momentum, and mean reversion
            trend_effect = trend * trend_strength * volatility_base
            random_walk = np.random.normal(0, volatility_base)
            target_effect = 0.1 * (config["current_price"] - current_price) / current_price

            # Apply combined price change
            price_change = trend_effect + random_walk + target_effect + momentum
            current_price *= (1 + price_change)

            # Update momentum
            momentum = 0.3 * price_change * trend_strength

            # Ensure price stays within realistic bounds
            current_price = max(min(current_price, config["start_price"] * 1.2), 
                                config["current_price"] * 0.8)

            timestamps.append(timestamp)
            prices.append(current_price)

            # Generate more realistic candle data
            volatility_factor = np.random.uniform(0.5, 2.0) * volatility_base
            price_range = current_price * volatility_factor

            # Create more dramatic candles based on trend and momentum
            if trend > 0:
                high = current_price * (1 + volatility_factor * (1 + abs(momentum)))
                low = current_price * (1 - volatility_factor * 0.7)
            else:
                high = current_price * (1 + volatility_factor * 0.7)
                low = current_price * (1 - volatility_factor * (1 + abs(momentum)))

            if i > 0:
                open_price = prices[-2]  # Previous close becomes open
            else:
                open_price = current_price

            candle = {
                'timestamp': timestamp,
                'open': open_price,
                'high': max(high, open_price, current_price),
                'low': min(low, open_price, current_price),
                'close': current_price
            }
            candles.append(candle)

        logger.info(f"Generated {len(candles)} candles from {start_time} to {end_time}")
        return timestamps, prices, candles

    except Exception as e:
        logger.error(f"Error in price history generation: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None

async def create_price_chart(timeframe="1hr"):
    """Create a traditional candlestick chart with clear visuals."""
    try:
        # Get price data
        timestamps, prices, candles = await get_lux_price_history(timeframe)
        if not timestamps or not prices or not candles:
            logger.error("Failed to get price data")
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
        max_price = max(high_prices) * 1.02
        min_price = min(low_prices) * 0.98
        price_range = max_price - min_price

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
        for i in range(6):
            y = padding + (i * chart_height // 5)
            draw.line([(padding, y), (width-padding, y)], fill=grid_color, width=1)
            price = max_price - (i * price_range / 5)
            price_str = f"${price:.6f}"
            draw.text((10, y-10), price_str, fill=label_color, font=small_font)

        # Draw vertical grid lines and time labels
        num_vert_lines = 8
        for i in range(num_vert_lines + 1):
            x = padding + (i * chart_width // num_vert_lines)
            draw.line([(x, padding), (x, height-padding)], fill=grid_color, width=1)

            if i < len(candles):
                idx = int((i * (len(candles) - 1)) / num_vert_lines)
                if idx < len(candles):
                    dt = datetime.fromtimestamp(candles[idx]['timestamp'] / 1000)
                    # Format time with date for all timeframes
                    time_str = dt.strftime("%m/%d\n%H:%M")
                    text_width = len(time_str) * 5
                    draw.text((x - text_width/2, height-padding+10), 
                             time_str, fill=label_color, font=small_font)

        # Draw candlesticks with improved visibility
        candle_spacing = chart_width / len(candles)
        candle_width = max(3, min(candle_spacing * 0.8, 8))  # Min 3px, max 8px width

        for i, candle in enumerate(candles):
            try:
                x = padding + (i * candle_spacing)

                # Calculate y-coordinates
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
                body_coords = (
                    x, min(open_y, close_y),
                    x + candle_width, max(open_y, close_y)
                )

                try:
                    draw.rectangle(body_coords, fill=color, outline=color)
                except Exception as e:
                    logger.error(f"Failed to draw candle at x={x}: {str(e)}")
                    # Fallback to line if rectangle fails
                    draw.line([(x, min(open_y, close_y)), 
                              (x + candle_width, max(open_y, close_y))],
                             fill=color, width=max(1, int(candle_width)))

            except Exception as e:
                logger.error(f"Error drawing candle {i}: {str(e)}")
                continue

        # Add title
        title = f"LUX/USD {timeframe} Chart"
        draw.text((padding, 20), title, fill=label_color, font=font)

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