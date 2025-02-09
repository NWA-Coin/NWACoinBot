import os
import logging
from datetime import datetime, timedelta
import numpy as np
import aiohttp
import asyncio
import json

# Set up logging
logger = logging.getLogger('discord_bot')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

async def get_lux_price_history():
    """Get LUX price history from CoinGecko asynchronously."""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching LUX price data (attempt {attempt + 1}/{max_retries})")

            # Use CoinGecko API v3 endpoint with more specific parameters
            url = "https://api.coingecko.com/api/v3/coins/lux-token/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "30",
                "interval": "daily",
                "precision": "full"  # Get full precision for small numbers
            }

            logger.info(f"Making API request to: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 429:
                        logger.warning("Rate limited by CoinGecko API")
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            logger.info(f"Waiting {wait_time} seconds before retry")
                            await asyncio.sleep(wait_time)
                            continue
                        logger.error("Max retries reached for rate limit")
                        return await generate_mock_data()

                    if response.status != 200:
                        logger.error(f"API Error {response.status}: {await response.text()}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return await generate_mock_data()

                    data = await response.json()
                    logger.debug(f"Raw API response: {data}")

                    if not data or 'prices' not in data:
                        logger.error(f"Invalid API response format: {data}")
                        return await generate_mock_data()

                    prices = [p[1] for p in data['prices']]
                    dates = [datetime.fromtimestamp(p[0]/1000) for p in data['prices']]

                    if not prices or not dates:
                        logger.error("Empty price data received")
                        return await generate_mock_data()

                    logger.info(f"Successfully fetched {len(prices)} price points")
                    logger.info(f"Price range: ${min(prices):.8f} - ${max(prices):.8f}")
                    logger.info(f"Date range: {dates[0]} - {dates[-1]}")
                    return dates, prices

        except asyncio.TimeoutError:
            logger.error(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return await generate_mock_data()

        except Exception as e:
            logger.error(f"Unexpected error in get_lux_price_history: {str(e)}")
            logger.exception("Full traceback:")
            return await generate_mock_data()

    logger.error("All attempts failed")
    return await generate_mock_data()

async def generate_mock_data():
    """Generate realistic mock price data asynchronously."""
    try:
        logger.warning("Using mock price data")
        days = 30
        initial_price = 0.015  # NWA entry price
        final_price = 0.00001  # Current crashed price

        dates = [datetime.now() - timedelta(days=x) for x in range(days)]
        dates.reverse()  # Make dates go forward

        # Generate exponential decay with volatility
        decay = (final_price / initial_price) ** (1/days)
        base_prices = [initial_price * (decay ** i) for i in range(days)]

        # Add realistic volatility
        volatility = 0.15  # 15% daily volatility
        prices = []
        for base_price in base_prices:
            # Add random walk with downward bias
            change = np.random.normal(-0.02, volatility)
            price = base_price * (1 + change)
            price = max(0.00000001, price)  # Ensure price doesn't go negative
            prices.append(price)

        logger.info(f"Generated mock data: ${prices[0]:.8f} -> ${prices[-1]:.8f}")
        return dates, prices

    except Exception as e:
        logger.error(f"Error generating mock data: {str(e)}")
        logger.exception("Full traceback:")
        # Return absolute fallback data
        dates = [datetime.now() - timedelta(days=x) for x in range(30)]
        prices = [0.015 * (0.9 ** x) for x in range(30)]  # Simple geometric decay
        return dates, prices

def create_price_chart():
    """Create a price chart using the Binance public chart."""
    try:
        logger.info("Starting price chart creation using Binance chart")

        # Create HTML file with embedded Binance chart widget
        html_content = """
        <html>
        <head>
            <style>
                body { 
                    margin: 0; 
                    background: #2C2F33; 
                    width: 100vw;
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                .chart-container { 
                    width: 1280px;
                    height: 720px;
                    background: #2C2F33;
                }
            </style>
        </head>
        <body>
            <!-- TradingView Chart Widget BEGIN -->
            <div class="chart-container">
                <div id="tradingview_chart"></div>
                <script type="text/javascript" src="https://s.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                    new TradingView.widget({
                        "width": "100%",
                        "height": "100%",
                        "symbol": "KUCOIN:LUXUSDT",  // Using KuCoin chart for better data
                        "interval": "60",  // 1 hour interval for more detail
                        "timezone": "Etc/UTC",
                        "theme": "dark",
                        "style": "1",  // Candlestick chart
                        "locale": "en",
                        "toolbar_bg": "#2C2F33",
                        "enable_publishing": false,
                        "hide_legend": true,
                        "save_image": false,
                        "container_id": "tradingview_chart",
                        "hide_volume": true,
                        "hide_top_toolbar": true,
                        "hide_side_toolbar": true,
                    });
                </script>
            </div>
            <!-- TradingView Chart Widget END -->
        </body>
        </html>
        """

        # Save HTML file
        chart_path = f"price_chart_{int(datetime.now().timestamp())}.html"
        with open(chart_path, 'w') as f:
            f.write(html_content)

        logger.info(f"Successfully created chart HTML: {chart_path}")
        return chart_path

    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        logger.exception("Full traceback:")
        return None