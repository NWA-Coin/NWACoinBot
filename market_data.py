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

# Rate limiting configuration for free tier
MIN_API_INTERVAL = 30  # Minimum seconds between API calls for free tier
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

async def fetch_lux_market_data(timeframe="1hr") -> Tuple[Optional[List[int]], Optional[List[float]], Optional[List[Dict]]]:
    """Fetch live LUX market data from CoinGecko API with retries."""
    try:
        # Map timeframes to days for free API
        timeframe_map = {
            "5m": "1",     # 1 day for 5m view
            "15m": "2",    # 2 days for 15m view
            "1hr": "3"     # 3 days for 1h view
        }

        days = timeframe_map.get(timeframe, "3")
        logger.info(f"Fetching {days} days of price data for timeframe {timeframe}")

        # Set timeout for API requests
        timeout = aiohttp.ClientTimeout(total=15)  # Increased timeout for free tier

        for retry in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"Attempt {retry + 1}/{MAX_RETRIES} to fetch market data")

                    endpoint = f"{COINGECKO_BASE_URL}/coins/{LUX_ID}/market_chart"
                    params = {
                        "vs_currency": "usd",
                        "days": days,
                        "interval": "hourly"  # Free tier supports hourly data
                    }

                    # Add demo API key if available
                    if COINGECKO_API_KEY:
                        params["x_cg_pro_api_key"] = COINGECKO_API_KEY
                        logger.info("Using CoinGecko demo API key")

                    logger.info(f"Requesting data from {endpoint}")
                    async with session.get(endpoint, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info("Received response from CoinGecko API")

                            if not data or "prices" not in data:
                                logger.error("Invalid response format from CoinGecko")
                                if retry < MAX_RETRIES - 1:
                                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                continue

                            price_data = data["prices"]
                            if not price_data:
                                logger.error("No price data received")
                                if retry < MAX_RETRIES - 1:
                                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                continue

                            timestamps = []
                            prices = []
                            candles = []

                            for timestamp, price in price_data:
                                # Validate data points
                                if not isinstance(timestamp, (int, float)) or not isinstance(price, (int, float)):
                                    logger.warning(f"Invalid data point: ts={timestamp}, price={price}")
                                    continue

                                ts = int(timestamp)
                                price = float(price)

                                # Skip invalid prices
                                if price <= 0:
                                    logger.warning(f"Invalid price value: {price} at {ts}")
                                    continue

                                timestamps.append(ts)
                                prices.append(price)

                                # Generate candle data with smaller variations for stability
                                candle = {
                                    'timestamp': ts,
                                    'open': price,
                                    'high': price * 1.002,  # 0.2% variation
                                    'low': price * 0.998,   # 0.2% variation
                                    'close': price
                                }
                                candles.append(candle)

                            if len(candles) < 2:
                                logger.error("Insufficient price data points")
                                if retry < MAX_RETRIES - 1:
                                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                continue

                            logger.info(f"Successfully processed {len(candles)} price points")
                            logger.info(f"Latest price: ${prices[-1]:.6f}")
                            return timestamps, prices, candles

                        elif response.status == 429:
                            logger.warning("Rate limit hit, waiting before retry")
                            # Wait longer for rate limit on free tier
                            await asyncio.sleep(MIN_API_INTERVAL)
                        else:
                            logger.error(f"API request failed with status {response.status}")
                            response_text = await response.text()
                            logger.error(f"Error response: {response_text}")
                            if retry < MAX_RETRIES - 1:
                                await asyncio.sleep(RETRY_DELAY * (retry + 1))

            except asyncio.TimeoutError:
                logger.error(f"Request timeout on attempt {retry + 1}")
                if retry < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
            except Exception as e:
                logger.error(f"Error during API request: {str(e)}")
                if retry < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (retry + 1))

        logger.error("All attempts to fetch market data failed")
        return None, None, None

    except Exception as e:
        logger.error(f"Unexpected error in fetch_lux_market_data: {str(e)}")
        logger.exception("Full traceback:")
        return None, None, None