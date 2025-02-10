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
            "1hr": "1",     # 1 day of data (we'll filter to last hour)
            "24hr": "2",    # 2 days of data
            "7d": "7",     # 7 days of data
            "1m": "30",    # 30 days of data
            "3m": "90"     # 90 days of data
        }

        days = timeframe_map.get(timeframe, "2")  # Default to 2 days if timeframe not found
        logger.info(f"Fetching {days} days of price data for timeframe {timeframe}")

        timeout = aiohttp.ClientTimeout(total=15)

        for retry in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"Attempt {retry + 1}/{MAX_RETRIES} to fetch market data")

                    params = {
                        "vs_currency": "usd",
                        "days": days,
                    }

                    headers = {}
                    if COINGECKO_API_KEY:
                        headers["x-cg-demo-api-key"] = COINGECKO_API_KEY
                        logger.info("Using CoinGecko API key")

                    endpoint = f"{COINGECKO_BASE_URL}/coins/{LUX_ID}/market_chart"
                    logger.info(f"Requesting data from {endpoint}")

                    async with session.get(endpoint, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info("Successfully parsed JSON response")

                            if not data or "prices" not in data:
                                logger.error("Invalid response format")
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
                            if timeframe == "1hr":
                                cutoff_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
                                price_data = [p for p in price_data if p[0] >= cutoff_time]
                                logger.info(f"Filtered to last hour: {len(price_data)} points")

                            # Ensure minimum number of data points
                            if len(price_data) < 2:
                                logger.error("Insufficient data points after filtering")
                                if retry < MAX_RETRIES - 1:
                                    await asyncio.sleep(RETRY_DELAY * (retry + 1))
                                continue

                            timestamps = []
                            prices = []

                            # Process data points
                            for point in price_data:
                                timestamp = int(point[0])
                                price = float(point[1])
                                timestamps.append(timestamp)
                                prices.append(price)

                            logger.info(f"Successfully processed {len(timestamps)} price points")
                            logger.info(f"Latest price: ${prices[-1]:.6f}")
                            return timestamps, prices, None

                        elif response.status == 429:
                            logger.warning("Rate limit hit, waiting before retry")
                            await asyncio.sleep(MIN_API_INTERVAL)
                        else:
                            logger.error(f"API request failed with status {response.status}")
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