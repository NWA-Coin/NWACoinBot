import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import time
import logging

# Set up logging
logger = logging.getLogger('discord_bot')

def fetch_lux_price(max_retries=3):
    """Fetch current price for LUX token from CoinGecko with retries."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching LUX price data from CoinGecko (attempt {attempt + 1}/{max_retries})...")
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "luxfi",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true"
                },
                headers={
                    "accept": "application/json"
                },
                timeout=10
            )

            logger.info(f"API Response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if 'luxfi' in data:
                    price = data['luxfi']['usd']
                    # Handle case where 24h change is null
                    change_24h = data['luxfi'].get('usd_24h_change')
                    if change_24h is None:
                        change_24h = -99.99  # Assume the worst for maximum roasting potential
                        logger.warning("24h change data missing, using default negative value")
                    logger.info(f"Current price: ${price:.8f} (24h change: {change_24h:.2f}%)")
                    return price, change_24h
                logger.warning("No price data in API response")
            elif response.status_code == 429:
                logger.warning("Rate limit hit, waiting before retry...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                logger.error(f"API returned status code {response.status_code}")

            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry

        except Exception as e:
            logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)

    logger.error("All attempts failed to fetch price")
    return 0.00000001, -99.99  # Return ultra-low price and big negative change on failure

def generate_price_chart():
    """Generate a price chart for LUX token."""
    try:
        price, change = fetch_lux_price()

        # Create simple price display
        plt.figure(figsize=(8, 6), dpi=100)

        # Create text-based display with bigger red text for bad performance
        plt.text(0.5, 0.6, f"Current LUX Price: ${price:.8f}", 
                horizontalalignment='center', fontsize=16, 
                color='red' if price < 0.0001 else 'black')

        # If change is None or invalid, use a custom message
        if change == -99.99:
            change_text = "24h Change: Unknown (probably rekt) 💀"
        else:
            change_text = f"24h Change: {change:+.2f}%"

        plt.text(0.5, 0.4, change_text,
                horizontalalignment='center', fontsize=14,
                color='red')

        # Add some NWA-themed flavor text based on performance
        if change < -10 or change == -99.99:
            plt.text(0.5, 0.2, "Straight Outta Profits! 💀🎤",
                    horizontalalignment='center', fontsize=12, color='red')
        elif price < 0.0001:
            plt.text(0.5, 0.2, "Worth less than NWA's first mixtape! 📼💀",
                    horizontalalignment='center', fontsize=12, color='red')

        # Remove axes for cleaner look
        plt.axis('off')

        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()

        buffer.seek(0)
        logger.info("Price chart generated successfully")
        return buffer
    except Exception as e:
        logger.error(f"Error generating price chart: {str(e)}")

        # Create error message chart with NWA reference
        plt.figure(figsize=(8, 6), dpi=100)
        plt.text(0.5, 0.5, "❌ Failed to get price data\nBut LUX still weak like a bootleg mixtape! 💀🎤",
                horizontalalignment='center', fontsize=14, color='red')
        plt.axis('off')

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()

        buffer.seek(0)
        return buffer