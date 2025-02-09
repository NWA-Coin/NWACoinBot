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
LUX_ID = "lux-token"  # Updated CoinGecko asset ID for LUX token

# Add rate limiting and retry configuration
last_api_call = datetime.min
MIN_API_INTERVAL = 2  # Minimum seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

async def fetch_lux_market_data(timeframe="1hr") -> Tuple[Optional[List[int]], Optional[List[float]], Optional[List[Dict]]]:
    """Fetch live LUX market data from CoinGecko API with retries."""
    try:
        global last_api_call

        # Rate limiting
        now = datetime.now()
        time_since_last_call = (now - last_api_call).total_seconds()
        if time_since_last_call < MIN_API_INTERVAL:
            await asyncio.sleep(MIN_API_INTERVAL - time_since_last_call)

        last_api_call = now

        # Map timeframes to days for CoinGecko API
        timeframe_map = {
            "5m": "1",     # 1 day for 5m view
            "15m": "1",    # 1 day for 15m view
            "1hr": "3"     # 3 days for 1h view
        }

        # Get correct days parameter or default to 3 days
        days = timeframe_map.get(timeframe, "3")
        logger.info(f"Using {days} days for timeframe {timeframe}")

        # Set timeout for API requests
        timeout = aiohttp.ClientTimeout(total=10)

        # Implement retry logic
        for retry in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logger.info(f"Attempting to fetch market data (attempt {retry + 1}/{MAX_RETRIES})")

                    # Construct API endpoint with proper parameters
                    endpoint = f"{COINGECKO_BASE_URL}/coins/{LUX_ID}/market_chart"
                    params = {
                        "vs_currency": "usd",
                        "days": days,
                        "precision": "full"
                    }

                    # Add API key if available
                    if COINGECKO_API_KEY:
                        params["x_cg_demo_api_key"] = COINGECKO_API_KEY

                    logger.info(f"Requesting data from {endpoint} with params: {params}")
                    async with session.get(endpoint, params=params) as response:
                        response_text = await response.text()
                        logger.info(f"API Response Status: {response.status}")
                        logger.info(f"API Response: {response_text[:200]}...")  # Log first 200 chars

                        if response.status == 200:
                            data = await response.json()

                            if not data or "prices" not in data:
                                logger.error("Received invalid data from CoinGecko API")
                                logger.error(f"Response data structure: {data.keys() if data else None}")
                                continue

                            # Process price data
                            timestamps = []
                            prices = []
                            candles = []

                            price_data = data["prices"]  # [[timestamp, price], ...]
                            logger.info(f"Retrieved {len(price_data)} price points")
                            logger.info(f"First price point: {price_data[0] if price_data else None}")
                            logger.info(f"Last price point: {price_data[-1] if price_data else None}")

                            for i, [timestamp, price] in enumerate(price_data):
                                try:
                                    # Convert timestamp from milliseconds
                                    ts = int(timestamp)
                                    price = float(price)

                                    # Skip if price is invalid
                                    if price <= 0:
                                        logger.warning(f"Invalid price {price} at timestamp {ts}")
                                        continue

                                    timestamps.append(ts)
                                    prices.append(price)

                                    # Calculate OHLC for candle with more realistic variations
                                    variation = price * 0.005  # 0.5% variation
                                    candle = {
                                        'timestamp': ts,
                                        'open': price,
                                        'high': price + variation,
                                        'low': price - variation,
                                        'close': price
                                    }
                                    candles.append(candle)

                                    # Log some sample data points
                                    if i == 0 or i == len(price_data) - 1:
                                        logger.info(f"Processed data point {i}: ts={ts}, price={price:.8f}")

                                except (ValueError, TypeError) as e:
                                    logger.error(f"Error processing price data: {str(e)}")
                                    continue

                            if not timestamps:
                                logger.error("No valid prices processed")
                                continue

                            logger.info(f"Successfully fetched {len(candles)} candles of live market data")
                            return timestamps, prices, candles

                        else:
                            logger.error(f"CoinGecko API request failed with status {response.status}: {response_text}")

                    if retry < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_DELAY * (retry + 1))

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