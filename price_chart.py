import os
import logging
from datetime import datetime, timedelta
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import asyncio
import json

# Set up logging
logger = logging.getLogger('discord_bot')

async def get_lux_price_history(timeframe="1hr"):
    """Get LUX price history from API with specified timeframe."""
    max_retries = 3
    retry_delay = 2
    last_error = None

    # Configure timeframes for proper historical data
    timeframe_config = {
        "5m": {"days": "0.5", "interval": "5m"},    # 12 hours of 5-min candles
        "15m": {"days": "1", "interval": "15m"},    # 24 hours of 15-min candles
        "1hr": {"days": "3", "interval": "1h"}      # 3 days of 1-hour candles
    }

    config = timeframe_config.get(timeframe, timeframe_config["1hr"])

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching LUX price data (attempt {attempt + 1}/{max_retries}) for timeframe {timeframe}")

            token_id = "luxfi"
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
                params = {
                    "vs_currency": "usd",
                    "days": config["days"],
                    "interval": config["interval"],
                    "precision": "full"
                }

                logger.info(f"Trying CoinGecko API with token ID: {token_id}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'prices' in data:
                                # Get only recent data based on timeframe
                                dates = [p[0] for p in data['prices']]
                                prices = [p[1] for p in data['prices']]

                                # Create candles from price data
                                candles = []
                                for i in range(0, len(prices), 2):
                                    chunk_prices = prices[i:i+2]
                                    if chunk_prices:
                                        candle = {
                                            'timestamp': dates[i],
                                            'open': chunk_prices[0],
                                            'high': max(chunk_prices),
                                            'low': min(chunk_prices),
                                            'close': chunk_prices[-1]
                                        }
                                        candles.append(candle)

                                logger.info(f"Successfully fetched price data. Latest price: ${prices[-1]:.6f}")
                                return dates, prices, candles

            except Exception as e:
                last_error = e
                logger.warning(f"Failed to fetch data: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue

            logger.warning(f"CoinGecko attempt failed: {str(last_error)}")
            return await generate_mock_data(timeframe)

        except Exception as e:
            last_error = e
            logger.error(f"Error in get_lux_price_history: {str(e)}")
            logger.exception("Full traceback:")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return await generate_mock_data(timeframe)

    logger.error(f"All attempts failed. Last error: {str(last_error)}")
    return await generate_mock_data(timeframe)

async def generate_mock_data(timeframe="1hr"):
    """Generate realistic mock price data with specified timeframe."""
    try:
        logger.warning(f"=== Using mock price data for timeframe {timeframe} ===")

        # Configure periods based on timeframe for recent data
        timeframe_config = {
            "5m": {
                "periods": 144,    # 12 hours (144 * 5min = 720min = 12h)
                "price": 0.0048,   # Price from 12h ago
                "volatility": 0.003
            },
            "15m": {
                "periods": 96,     # 24 hours (96 * 15min = 1440min = 24h)
                "price": 0.0052,   # Price from 24h ago
                "volatility": 0.005
            },
            "1hr": {
                "periods": 72,     # 3 days (72 * 1h = 72h = 3d)
                "price": 0.015,    # NWA entry price (3d ago)
                "volatility": 0.008
            }
        }

        config = timeframe_config.get(timeframe, timeframe_config["1hr"])
        periods = config["periods"]
        start_price = config["price"]
        base_volatility = config["volatility"]
        current_price = 0.0037  # Current price

        # Calculate and log crash percentage for verification
        crash_percent = ((start_price - current_price) / start_price) * 100
        price_in_cents = current_price * 100

        logger.info(f"=== Mock Data Configuration ===")
        logger.info(f"Timeframe: {timeframe}")
        logger.info(f"Number of periods: {periods}")
        logger.info(f"Start price: ${start_price:.6f} ({start_price*100:.2f}¢)")
        logger.info(f"Current price: ${current_price:.6f} ({current_price*100:.2f}¢)")
        logger.info(f"Crash percentage: Down {crash_percent:.1f}% from start")

        dates = []
        prices = []
        candles = []

        # Calculate price decay with improved exponential decay
        price_decay = (current_price / start_price) ** (1.0 / periods)
        logger.info(f"Price decay factor per period: {price_decay:.8f}")

        # Calculate time delta based on timeframe
        time_deltas = {
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1hr": timedelta(hours=1)
        }
        delta = time_deltas.get(timeframe, timedelta(hours=1))

        # Generate price data with proper timestamps
        logger.info(f"=== Generating {periods} candles ===")
        now = datetime.now()
        interval = delta.total_seconds()

        for i in range(periods):
            # Calculate exact timestamp for this interval
            current_timestamp = int(now.timestamp())
            # Round down to nearest interval
            base_timestamp = current_timestamp - (current_timestamp % int(interval))
            timestamp = int((base_timestamp - (periods - i - 1) * interval) * 1000)

            # Format timestamp for logging
            dt = datetime.fromtimestamp(timestamp/1000)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")

            # Calculate target price with exponential decay
            target_price = start_price * (price_decay ** i)

            # Add volatility that increases as price drops
            volatility_factor = 1 + (crash_percent / 100)  # Volatility increases with crash %
            period_volatility = base_volatility * volatility_factor

            if i == 0:
                price = start_price
                logger.info(f"First candle - Time: {formatted_time}, Price: ${price:.6f}")
            else:
                # Random walk with mean reversion to target price
                price_diff = target_price - prices[-1]
                mean_reversion = 0.3  # 30% reversion to target
                random_walk = np.random.normal(0, period_volatility)
                price = prices[-1] + (price_diff * mean_reversion) + (target_price * random_walk)

                # Ensure price stays within realistic bounds
                price = max(min(price, start_price), current_price * 0.95)

            # Log key points in the data generation
            if i == 0 or i == periods//2 or i == periods-1:
                logger.info(f"Candle {i+1}/{periods} - Time: {formatted_time}, Price: ${price:.6f}")

            dates.append(timestamp)
            prices.append(price)

            # Generate OHLC data with proper volatility
            if i > 0:
                prev_price = prices[-2]
                high_price = max(price, prev_price) * (1 + abs(np.random.normal(0, period_volatility/2)))
                low_price = min(price, prev_price) * (1 - abs(np.random.normal(0, period_volatility/2)))
            else:
                high_price = price * (1 + period_volatility/2)
                low_price = price * (1 - period_volatility/2)

            candle = {
                'timestamp': timestamp,
                'open': prices[-1] if i > 0 else price,
                'high': high_price,
                'low': low_price,
                'close': price
            }
            candles.append(candle)

        logger.info(f"=== Mock Data Generation Complete ===")
        logger.info(f"Generated {len(candles)} candles from {datetime.fromtimestamp(dates[0]/1000).strftime('%Y-%m-%d %H:%M:%S')} to {datetime.fromtimestamp(dates[-1]/1000).strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Final price range: ${prices[0]:.6f} -> ${prices[-1]:.6f}")
        return dates, prices, candles

    except Exception as e:
        logger.error(f"Error generating mock data: {str(e)}")
        logger.exception("Full traceback:")
        return [], [], []

async def create_price_chart(timeframe="1hr"):
    """Create a candlestick chart using PIL."""
    try:
        logger.info(f"Starting candlestick chart creation for timeframe {timeframe}")

        # Get price data asynchronously
        dates, prices, candles = await get_lux_price_history(timeframe)

        if not candles:
            logger.error("No candlestick data available")
            raise Exception("Failed to get candlestick data")

        # Create new image with dark background
        width = 1280
        height = 720
        img = Image.new('RGB', (width, height), '#1E2124')  # Darker background
        draw = ImageDraw.Draw(img)

        # Calculate chart dimensions
        padding = 60
        chart_width = width - (2 * padding)
        chart_height = height - (2 * padding)

        # Calculate price range with padding
        high_prices = [c['high'] for c in candles]
        low_prices = [c['low'] for c in candles]
        max_price = max(high_prices) * 1.02  # Add 2% padding
        min_price = min(low_prices) * 0.98   # Subtract 2% padding
        price_range = max_price - min_price

        # Load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except Exception:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw grid lines and price labels
        grid_color = '#2F3136'  # Slightly lighter than background
        for i in range(6):  # Increase number of grid lines
            y = padding + (i * chart_height // 5)
            draw.line([(padding, y), (width-padding, y)], fill=grid_color, width=1)
            price = max_price - (i * price_range / 5)
            price_str = f"${price:.6f}"
            draw.text((10, y-10), price_str, fill='#FFFFFF', font=small_font)

        # Draw vertical grid lines for time
        num_vert_lines = 8
        for i in range(num_vert_lines + 1):
            x = padding + (i * chart_width // num_vert_lines)
            draw.line([(x, padding), (x, height-padding)], fill=grid_color, width=1)

        # Calculate candle dimensions
        num_candles = len(candles)
        spacing = (chart_width / num_candles) * 0.2  # 20% of space between candles
        candle_width = (chart_width / num_candles) * 0.8  # 80% of space for candle

        # Draw time labels with proper formatting
        for i in range(num_vert_lines + 1):
            x = padding + (i * chart_width // num_vert_lines)
            idx = int((i * (len(candles) - 1)) / num_vert_lines)
            if idx < len(candles):
                timestamp = candles[idx]['timestamp'] / 1000
                dt = datetime.fromtimestamp(timestamp)

                # Format time based on timeframe
                if timeframe == "5m":
                    time_str = dt.strftime("%H:%M")
                elif timeframe == "15m":
                    time_str = dt.strftime("%H:%M")
                else:  # 1hr
                    time_str = dt.strftime("%m/%d\n%H:%M")

                # Center text under grid line
                text_width = len(time_str) * 5
                draw.text((x - text_width/2, height-padding+10), time_str, fill='#FFFFFF', font=small_font)

        # Draw candlesticks
        for i, candle in enumerate(candles):
            x = padding + (i * (candle_width + spacing))

            # Calculate y coordinates
            open_y = padding + ((max_price - candle['open']) * chart_height / price_range)
            close_y = padding + ((max_price - candle['close']) * chart_height / price_range)
            high_y = padding + ((max_price - candle['high']) * chart_height / price_range)
            low_y = padding + ((max_price - candle['low']) * chart_height / price_range)

            # Determine candle color
            color = '#FF4444' if candle['close'] < candle['open'] else '#44FF44'

            # Draw wick
            wick_x = x + candle_width/2
            draw.line([(wick_x, high_y), (wick_x, low_y)], fill=color, width=2)

            # Draw candle body
            body_top = min(open_y, close_y)
            body_bottom = max(open_y, close_y)
            body_height = max(1, body_bottom - body_top)  # Ensure minimum height of 1 pixel

            draw.rectangle(
                [(x, body_top), (x + candle_width, body_bottom)],
                fill=color,
                outline=color
            )

        # Add chart title
        title = f"LUX/USD {timeframe} Chart"
        draw.text((padding, 20), title, fill='#FFFFFF', font=font)

        # Save chart
        chart_path = f"price_chart_{int(datetime.now().timestamp())}.png"
        img.save(chart_path, quality=95)

        logger.info(f"Successfully created candlestick chart: {chart_path}")
        return chart_path

    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.exception("Full traceback:")
        return None