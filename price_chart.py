import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
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
                        # Extract timestamps and prices
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
    start_price = end_price * 10  # 10x higher start price for dramatic effect
    timestamps = [datetime.now() - timedelta(days=i) for i in range(days, -1, -1)]
    prices = np.linspace(start_price, end_price, len(timestamps))
    return timestamps, prices

def fetch_current_price(max_retries=3):
    """Fetch current price for LUX token from CoinGecko with retries."""
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
                        price = float(data['luxfi']['usd'])  # Ensure float conversion
                        change_24h = data['luxfi'].get('usd_24h_change')
                        if change_24h is None:
                            change_24h = -99.99
                            logger.warning("24h change missing, using default negative value")
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
    """Generate a price chart for LUX token with historical data."""
    try:
        # Get current price and historical data
        current_price, change = fetch_current_price()
        timestamps, prices = fetch_historical_prices()

        # Convert prices to cents for better readability
        prices_in_cents = [price * 100 for price in prices]
        current_price_cents = current_price * 100

        # Set dark theme
        plt.style.use('dark_background')

        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12), gridspec_kw={'height_ratios': [2, 1]})
        fig.patch.set_facecolor('#1E1E1E')  # Dark background

        # Plot historical prices
        ax1.plot(timestamps, prices_in_cents, '#FF4444', linewidth=2, label='Price (cents)')
        ax1.grid(True, which="both", ls="-", alpha=0.2, color='gray')
        ax1.set_facecolor('#2D2D2D')  # Slightly lighter dark background

        # Format x-axis to show dates nicely
        ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax1.get_xticklabels(), rotation=45, color='white')
        plt.setp(ax1.get_yticklabels(), color='white')

        # Set titles and labels with white text
        ax1.set_title("LUX Price History (Last 7 Days)", color='white', fontsize=14, pad=20)
        ax1.set_xlabel("Date", color='white', fontsize=12)
        ax1.set_ylabel("Price (cents)", color='white', fontsize=12)

        # Add price summary text
        summary_text = (
            f"Current Price: ${current_price:.12f}\n"
            f"Price in Cents: {current_price_cents:.6f}¢\n"
            f"24h Change: {change:+.2f}% 🚮"
        )
        ax2.text(0.5, 0.7, summary_text, 
                horizontalalignment='center', 
                fontsize=16, 
                color='#FF4444',
                fontweight='bold')
        ax2.set_facecolor('#2D2D2D')

        # Add NWA-themed roast based on performance
        if change < -10 or change == -99.99:
            roast = "Straight Outta Value!\nDown BAD Like NWA's Lost Mixtapes! 💀🎤"
        elif current_price_cents < 0.01:
            roast = "Worth Less Than A Bootleg\nNWA Tape From Compton! 📼💀"
        else:
            roast = "More Worthless Than Ice Cube's\nKid Movie Career! 🎬💀"

        ax2.text(0.5, 0.3, roast,
                horizontalalignment='center',
                fontsize=14,
                color='#FF4444')

        # Remove axes from bottom subplot
        ax2.axis('off')

        # Adjust layout
        plt.tight_layout()

        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100, 
                   facecolor='#1E1E1E', edgecolor='none')
        plt.close(fig)

        buffer.seek(0)
        logger.info("Price chart generated successfully")
        return buffer

    except Exception as e:
        logger.error(f"Error generating price chart: {str(e)}")

        # Create error message chart with NWA reference
        plt.style.use('dark_background')
        plt.figure(figsize=(10, 8))
        plt.text(0.5, 0.5,
                "❌ Failed to Generate Price Chart\nBut LUX Still Weak Like Ice Cube's\nKid Movie Career! 💀🎤",
                horizontalalignment='center',
                fontsize=14,
                color='#FF4444')
        plt.axis('off')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100,
                   facecolor='#1E1E1E', edgecolor='none')
        plt.close()

        buffer.seek(0)
        return buffer