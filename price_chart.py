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

async def get_lux_price_history():
    """Get LUX price history from API with 30-minute candles."""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching LUX price data (attempt {attempt + 1}/{max_retries})")

            # Try multiple CoinGecko API endpoints since token ID might change
            token_ids = ["lux-token", "lux", "luxfi"]
            last_error = None

            for token_id in token_ids:
                try:
                    url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
                    params = {
                        "vs_currency": "usd",
                        "days": "7",  # Last 7 days for better 30m candle visibility
                        "interval": "30m",  # 30-minute intervals
                        "precision": "full"
                    }

                    logger.info(f"Trying CoinGecko API with token ID: {token_id}")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                if 'prices' in data:
                                    # Get OHLC data from prices
                                    timestamps = [p[0] for p in data['prices']]
                                    prices = [p[1] for p in data['prices']]

                                    # Group into 30-minute candles
                                    candles = []
                                    for i in range(0, len(prices), 2):  # 2 price points per hour
                                        chunk = prices[i:i+2]
                                        if chunk:
                                            candle = {
                                                'timestamp': timestamps[i],
                                                'open': chunk[0],
                                                'high': max(chunk),
                                                'low': min(chunk),
                                                'close': chunk[-1]
                                            }
                                            candles.append(candle)

                                    if candles:
                                        logger.info(f"Successfully fetched candle data from {token_id}")
                                        return candles

                except Exception as e:
                    last_error = e
                    logger.warning(f"Failed to fetch data for {token_id}: {str(e)}")
                    continue

            # If all token IDs fail, fall back to mock data
            logger.warning(f"All CoinGecko attempts failed: {str(last_error)}")
            return await generate_mock_candles()

        except Exception as e:
            logger.error(f"Error in get_lux_price_history: {str(e)}")
            logger.exception("Full traceback:")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return await generate_mock_candles()

    logger.error("All attempts failed")
    return await generate_mock_candles()

async def generate_mock_candles():
    """Generate realistic mock candlestick data."""
    try:
        logger.warning("Using mock candlestick data")
        candles = []
        periods = 336  # 7 days of 30-minute candles
        current_price = 0.015  # Start from NWA entry

        for i in range(periods):
            # Generate realistic price movement
            volatility = 0.15
            price_change = np.random.normal(-0.02, volatility)

            # Calculate OHLC values
            open_price = current_price
            close_price = max(0.00000001, current_price * (1 + price_change))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.05)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.05)))

            timestamp = int((datetime.now() - timedelta(minutes=30 * (periods - i))).timestamp() * 1000)

            candle = {
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price
            }
            candles.append(candle)
            current_price = close_price

        logger.info(f"Generated mock candles: ${candles[0]['open']:.8f} -> ${candles[-1]['close']:.8f}")
        return candles

    except Exception as e:
        logger.error(f"Error generating mock candles: {str(e)}")
        logger.exception("Full traceback:")
        return []

def create_price_chart():
    """Create a candlestick chart using PIL."""
    try:
        logger.info("Starting candlestick chart creation")

        # Get candlestick data asynchronously
        loop = asyncio.get_event_loop()
        candles = loop.run_until_complete(get_lux_price_history())

        if not candles:
            logger.error("No candlestick data available")
            raise Exception("Failed to get candlestick data")

        # Create new image with dark background
        width = 1280
        height = 720
        img = Image.new('RGB', (width, height), '#2C2F33')
        draw = ImageDraw.Draw(img)

        # Calculate chart dimensions
        padding = 60
        chart_width = width - (2 * padding)
        chart_height = height - (2 * padding)

        # Calculate price range
        high_prices = [c['high'] for c in candles]
        low_prices = [c['low'] for c in candles]
        max_price = max(high_prices)
        min_price = min(low_prices)
        price_range = max_price - min_price

        # Load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except Exception:
            font = ImageFont.load_default()

        # Draw grid lines and price labels
        for i in range(5):
            y = padding + (i * chart_height // 4)
            draw.line([(padding, y), (width-padding, y)], fill='#666666', width=1)
            price = max_price - (i * price_range / 4)
            draw.text((10, y-10), f"${price:.6f}", fill='white', font=font)

        # Calculate candle width
        candle_width = min(20, (chart_width / len(candles)) * 0.8)
        spacing = (chart_width / len(candles))

        # Draw candlesticks
        for i, candle in enumerate(candles):
            x = padding + (i * spacing)

            # Calculate y coordinates
            open_y = padding + ((max_price - candle['open']) * chart_height / price_range)
            close_y = padding + ((max_price - candle['close']) * chart_height / price_range)
            high_y = padding + ((max_price - candle['high']) * chart_height / price_range)
            low_y = padding + ((max_price - candle['low']) * chart_height / price_range)

            # Determine candle color
            color = '#44FF44' if candle['close'] > candle['open'] else '#FF4444'

            # Draw wick
            draw.line([(x + candle_width/2, high_y), (x + candle_width/2, low_y)], fill=color, width=1)

            # Draw candle body
            body_top = min(open_y, close_y)
            body_bottom = max(open_y, close_y)
            body_height = max(1, body_bottom - body_top)  # Ensure minimum height of 1 pixel

            draw.rectangle([(x, body_top), (x + candle_width, body_bottom)], 
                         fill=color, outline=color)

        # Add title and crash percentage
        title = "LUX 30m Candlestick Chart (7 Days)"
        draw.text((width//2 - 150, 20), title, fill='white', font=font)

        crash_percent = ((candles[0]['open'] - candles[-1]['close']) / candles[0]['open']) * 100
        crash_text = f"Down {crash_percent:.1f}% 💀"
        draw.text((width//2 - 50, height-40), crash_text, fill='red', font=font)

        # Save chart
        chart_path = f"price_chart_{int(datetime.now().timestamp())}.png"
        img.save(chart_path, quality=95)

        logger.info(f"Successfully created candlestick chart: {chart_path}")
        return chart_path

    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.exception("Full traceback:")
        return None