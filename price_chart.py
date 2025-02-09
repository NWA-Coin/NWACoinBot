import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import time
import logging
import numpy as np

# Set up logging
logger = logging.getLogger('discord_bot')

def fetch_historical_prices(days=7, max_retries=3):
    """Fetch historical price data for LUX token."""
    backup_apis = [
        "https://api.coingecko.com/api/v3/coins/luxfi/market_chart",
        "https://pro-api.coingecko.com/api/v3/coins/luxfi/market_chart"
    ]

    for api_url in backup_apis:
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching historical price data from {api_url} (attempt {attempt + 1}/{max_retries})...")
                response = requests.get(
                    api_url,
                    params={
                        "vs_currency": "usd",
                        "days": str(days),
                        "interval": "daily"
                    },
                    headers={"accept": "application/json"},
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    if 'prices' in data and len(data['prices']) > 0:
                        timestamps = [datetime.fromtimestamp(price[0]/1000) for price in data['prices']]
                        prices = [price[1] for price in data['prices']]
                        return timestamps, prices
                    logger.warning("No historical price data in response")
                elif response.status_code == 429:
                    logger.warning("Rate limit hit, waiting before retry...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"API returned status code {response.status_code}")

                if attempt < max_retries - 1:
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error fetching historical data on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)

    # Generate fake downtrend data if all attempts fail
    logger.warning("Using fallback historical data")
    end_price = 0.00000001
    start_price = end_price * 10
    timestamps = [datetime.now() - timedelta(days=i) for i in range(days, -1, -1)]
    prices = np.linspace(start_price, end_price, len(timestamps))
    return timestamps, prices

def fetch_current_price(max_retries=3):
    """Fetch current price for LUX token."""
    backup_apis = [
        "https://api.coingecko.com/api/v3/simple/price",
        "https://pro-api.coingecko.com/api/v3/simple/price"
    ]

    for api_url in backup_apis:
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching current price from {api_url} (attempt {attempt + 1}/{max_retries})...")
                response = requests.get(
                    api_url,
                    params={
                        "ids": "luxfi",
                        "vs_currencies": "usd",
                        "include_24hr_change": "true"
                    },
                    headers={"accept": "application/json"},
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if 'luxfi' in data:
                        price = float(data['luxfi']['usd'])
                        change_24h = data['luxfi'].get('usd_24h_change', -99.99)
                        logger.info(f"Current price: ${price:.12f} (24h change: {change_24h:.2f}%)")
                        return price, change_24h
                    logger.warning("No price data in response")
                elif response.status_code == 429:
                    logger.warning("Rate limit hit, waiting before retry...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"API returned status code {response.status_code}")

                if attempt < max_retries - 1:
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)

    logger.error("All attempts failed to fetch current price")
    return 0.00000001, -99.99

def generate_price_chart():
    """Generate a price chart for LUX token."""
    try:
        # Get current price and historical data
        current_price, change = fetch_current_price()
        timestamps, prices = fetch_historical_prices()

        # Create figure with dark theme
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1E1E1E')
        ax.set_facecolor('#2D2D2D')

        # Plot the line
        ax.plot(timestamps, prices, color='#FF4444', linewidth=2)

        # Configure axes
        ax.grid(True, alpha=0.2)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        # Set labels
        ax.set_title(f"LUX Price Chart\nCurrent: ${current_price:.12f} | 24h Change: {change:+.2f}%",
                    color='white', pad=20)
        ax.set_xlabel("Date", color='white', labelpad=10)
        ax.set_ylabel("Price (USD)", color='white', labelpad=10)

        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100,
                   facecolor='#1E1E1E', edgecolor='none')
        plt.close(fig)

        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Error generating price chart: {str(e)}")
        return None