import os
import logging
import aiohttp
from datetime import datetime, timedelta
import pytz
import asyncio
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger('discord_bot')

# Constants for CoinGecko API
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
LUX_ID = "lux-token"  # CoinGecko asset ID for LUX token

# Rate limiting configuration
MIN_API_INTERVAL = 30  # Minimum seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

async def fetch_lux_market_data(timeframe="1hr") -> Tuple[Optional[List[int]], Optional[List[float]], Optional[List[Dict]]]:
    """Fetch live LUX market data from CoinGecko API with retries."""
    try:
        # Map timeframes to days for API request
        timeframe_map = {
            "5m": "2",     # 2 days of data
            "15m": "2",    # 2 days of data
            "1hr": "3"     # 3 days of data
        }

        days = timeframe_map.get(timeframe, "3")
        logger.info(f"Fetching {days} days of price data for timeframe {timeframe}")

        timeout = aiohttp.ClientTimeout(total=15)

        for retry in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"Attempt {retry + 1}/{MAX_RETRIES} to fetch market data")

                    # Build request parameters
                    params = {
                        "vs_currency": "usd",
                        "days": days,
                    }

                    # Demo API key handling
                    headers = {}
                    if COINGECKO_API_KEY:
                        # Use the correct header format for demo API key
                        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY
                        logger.info("Using CoinGecko demo API key in headers")

                    endpoint = f"{COINGECKO_BASE_URL}/coins/{LUX_ID}/market_chart"
                    logger.info(f"Requesting data from {endpoint}")

                    async with session.get(endpoint, params=params, headers=headers) as response:
                        response_text = await response.text()
                        logger.info(f"Response status: {response.status}")
                        logger.info(f"Response headers: {dict(response.headers)}")
                        logger.info(f"Response text preview: {response_text[:200]}...")

                        if response.status == 200:
                            try:
                                data = await response.json()
                                logger.info("Successfully parsed JSON response")

                                if not data or "prices" not in data:
                                    logger.error(f"Invalid response format: {response_text}")
                                    if retry < MAX_RETRIES - 1:
                                        await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                    continue

                                price_data = data["prices"]
                                logger.info(f"Received {len(price_data)} price points")

                                if not price_data:
                                    logger.error("Empty price data received")
                                    if retry < MAX_RETRIES - 1:
                                        await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                    continue

                                # Filter data points based on timeframe
                                if timeframe == "5m":
                                    cutoff_time = int((datetime.now() - timedelta(hours=12)).timestamp() * 1000)
                                    price_data = [p for p in price_data if p[0] >= cutoff_time]
                                elif timeframe == "15m":
                                    cutoff_time = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
                                    price_data = [p for p in price_data if p[0] >= cutoff_time]

                                logger.info(f"After filtering: {len(price_data)} price points")

                                timestamps = []
                                prices = []
                                candles = []

                                # Generate OHLC data with proper candle structure
                                for i in range(0, len(price_data) - 1):
                                    current_price = float(price_data[i][1])
                                    next_price = float(price_data[i + 1][1])
                                    timestamp = int(price_data[i][0])

                                    # Calculate realistic OHLC values
                                    price_range = abs(next_price - current_price)
                                    volatility = price_range * 0.5  # Use half the price movement for volatility

                                    high = max(current_price, next_price) + (volatility * 0.3)  # Add some volatility
                                    low = min(current_price, next_price) - (volatility * 0.3)   # Subtract some volatility

                                    candle = {
                                        'timestamp': timestamp,
                                        'open': current_price,
                                        'high': high,
                                        'low': low,
                                        'close': next_price
                                    }

                                    timestamps.append(timestamp)
                                    prices.append(current_price)
                                    candles.append(candle)

                                # Add the last price point
                                if price_data:
                                    timestamps.append(int(price_data[-1][0]))
                                    prices.append(float(price_data[-1][1]))

                                if len(candles) < 2:
                                    logger.error("Insufficient price data points")
                                    if retry < MAX_RETRIES - 1:
                                        await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                    continue

                                logger.info(f"Successfully processed {len(candles)} price points")
                                logger.info(f"Latest price: ${prices[-1]:.6f}")
                                return timestamps, prices, candles

                            except Exception as e:
                                logger.error(f"Error processing response: {str(e)}")
                                logger.error(f"Raw response: {response_text}")
                                if retry < MAX_RETRIES - 1:
                                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                continue

                        elif response.status == 429:
                            logger.warning("Rate limit hit, waiting before retry")
                            await asyncio.sleep(MIN_API_INTERVAL)
                        else:
                            logger.error(f"API request failed with status {response.status}")
                            logger.error(f"Error response: {response_text}")
                            if retry < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY * (retry + 1))

            except asyncio.TimeoutError:
                logger.error(f"Request timeout on attempt {retry + 1}")
                if retry < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
            except Exception as e:
                logger.error(f"Error during API request: {str(e)}")
                logger.exception("Full traceback:")
                if retry < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (retry + 1))

        logger.error("All attempts to fetch market data failed")
        return None, None, None

    except Exception as e:
        logger.error(f"Unexpected error in fetch_lux_market_data: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None