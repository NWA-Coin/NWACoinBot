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
    """Fetch live LUX market data from MEXC API with retries."""
    try:
        global last_api_call

        # Rate limiting
        now = datetime.now()
        time_since_last_call = (now - last_api_call).total_seconds()
        if time_since_last_call < MIN_API_INTERVAL:
            await asyncio.sleep(MIN_API_INTERVAL - time_since_last_call)

        last_api_call = now

        # Configure API endpoints for MEXC
        base_url = "https://api.mexc.com"
        symbol = "LUXUSDT"  # LUX/USDT trading pair

        # Map timeframes to API intervals (MEXC uses different interval format)
        timeframe_map = {
            "5m": "5m",    # 12 hours of 5m candles
            "15m": "15m",  # 24 hours of 15m candles
            "1hr": "1h"    # 3 days of 1h candles
        }

        # Get correct interval or default to 1h
        interval = timeframe_map.get(timeframe, "1h")
        logger.info(f"Using interval {interval} for timeframe {timeframe}")

        # Configure candlestick limits
        limit_map = {
            "5m": 144,   # 12 hours
            "15m": 96,   # 24 hours
            "1hr": 72    # 3 days
        }
        limit = limit_map.get(timeframe, 72)

        # Set timeout for API requests
        timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds timeout

        # Implement retry logic
        for retry in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"Attempting to fetch market data (attempt {retry + 1}/{MAX_RETRIES})")

                    # Construct API endpoint with proper parameters
                    endpoint = f"{base_url}/api/v3/klines"
                    params = {
                        "symbol": symbol,
                        "interval": interval,
                        "limit": limit
                    }

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

                            for candle_data in data:
                                try:
                                    # MEXC Kline data format:
                                    # [timestamp, open, high, low, close, volume, ...]
                                    timestamp = int(candle_data[0])
                                    open_price = float(candle_data[1])
                                    high_price = float(candle_data[2])
                                    low_price = float(candle_data[3])
                                    close_price = float(candle_data[4])

                                    # Validate price data
                                    if any(p <= 0 for p in [open_price, high_price, low_price, close_price]):
                                        logger.warning(f"Invalid price data at timestamp {timestamp}")
                                        continue

                                    # Verify OHLC relationships
                                    if not (low_price <= open_price <= high_price and 
                                          low_price <= close_price <= high_price):
                                        logger.warning(f"Invalid OHLC relationships at timestamp {timestamp}")
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