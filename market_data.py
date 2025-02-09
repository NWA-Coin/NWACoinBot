import os
import logging
import aiohttp
from datetime import datetime, timedelta
import pytz
import asyncio
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger('discord_bot')

# Add rate limiting and retry configuration
last_api_call = datetime.min
MIN_API_INTERVAL = 2  # Minimum seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

async def fetch_lux_market_data(timeframe="1hr") -> Tuple[Optional[List[int]], Optional[List[float]], Optional[List[Dict]]]:
    """Fetch live LUX market data from API with retries."""
    try:
        global last_api_call

        # Rate limiting
        now = datetime.now()
        time_since_last_call = (now - last_api_call).total_seconds()
        if time_since_last_call < MIN_API_INTERVAL:
            await asyncio.sleep(MIN_API_INTERVAL - time_since_last_call)

        last_api_call = now

        # Configure API endpoint
        base_url = "https://api.mexc.com"
        symbol = "LUXUSDT"  # LUX/USDT trading pair

        # Map timeframes to API intervals
        interval_map = {
            "5m": "5m",
            "15m": "15m",
            "1hr": "1h"
        }

        interval = interval_map.get(timeframe, "1h")

        # Calculate time range based on timeframe
        end_time = datetime.now(pytz.UTC)
        if timeframe == "5m":
            start_time = end_time - timedelta(hours=12)
        elif timeframe == "15m":
            start_time = end_time - timedelta(days=1)
        else:
            start_time = end_time - timedelta(days=3)

        # Convert timestamps to milliseconds
        start_ts = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)

        # Construct API endpoint with proper parameters
        endpoint = f"{base_url}/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000  # Maximum data points
        }

        # Set timeout for API requests
        timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds timeout

        # Implement retry logic
        for retry in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"Attempting to fetch market data (attempt {retry + 1}/{MAX_RETRIES})")
                    async with session.get(endpoint, params=params) as response:
                        if response.status == 200:
                            data = await response.json()

                            if not data:
                                logger.error("Received empty data from API")
                                continue  # Try next retry

                            # Process candlestick data
                            timestamps = []
                            prices = []
                            candles = []

                            for candle in data:
                                try:
                                    # MEXC API returns: [timestamp, open, high, low, close, volume, ...]
                                    timestamp = int(candle[0])  # Open time
                                    open_price = float(candle[1])
                                    high_price = float(candle[2])
                                    low_price = float(candle[3])
                                    close_price = float(candle[4])

                                    # Validate price data
                                    if any(p <= 0 for p in [open_price, high_price, low_price, close_price]):
                                        logger.warning(f"Invalid price data in candle: {candle}")
                                        continue

                                    # Additional validation
                                    if high_price < low_price or open_price > high_price or open_price < low_price:
                                        logger.warning(f"Invalid price relationships in candle: {candle}")
                                        continue

                                    timestamps.append(timestamp)
                                    prices.append(close_price)
                                    candles.append({
                                        'timestamp': timestamp,
                                        'open': open_price,
                                        'high': high_price,
                                        'low': low_price,
                                        'close': close_price
                                    })
                                except (IndexError, ValueError) as e:
                                    logger.error(f"Error processing candle data: {str(e)}")
                                    continue

                            if not timestamps:
                                logger.error("No valid candles processed")
                                continue  # Try next retry

                            logger.info(f"Successfully fetched {len(candles)} candles of live market data")
                            return timestamps, prices, candles
                        else:
                            logger.error(f"API request failed with status {response.status}: {await response.text()}")

                    if retry < MAX_RETRIES - 1:  # Don't sleep on last retry
                        await asyncio.sleep(RETRY_DELAY * (retry + 1))  # Exponential backoff

            except aiohttp.ClientError as e:
                logger.error(f"Network error on attempt {retry + 1}: {str(e)}")
                if retry < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
            except asyncio.TimeoutError:
                logger.error(f"Timeout on attempt {retry + 1}")
                if retry < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (retry + 1))

        logger.error("All retries failed to fetch market data")
        return None, None, None

    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None