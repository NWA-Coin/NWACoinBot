import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import time

def fetch_lux_price():
    """Fetch current price for LUX token from CoinGecko."""
    try:
        print("Fetching LUX price data from CoinGecko...")
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

        print(f"API Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if 'luxfi' in data:
                price = data['luxfi']['usd']
                change_24h = data['luxfi'].get('usd_24h_change', 0)
                print(f"Current price: ${price:.8f} (24h change: {change_24h:.2f}%)")
                return price, change_24h
            else:
                print("Error: No price data in API response")
        else:
            print(f"Error: API returned status code {response.status_code}")
            if response.status_code == 429:
                print("Rate limit exceeded. Please try again later.")
        return None, None
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None, None

def generate_price_chart():
    """Generate a price chart for LUX token."""
    try:
        price, change = fetch_lux_price()
        if not price:
            print("Error: Could not fetch current price")
            return None

        # Create simple price display
        plt.figure(figsize=(8, 6), dpi=100)

        # Create text-based display
        plt.text(0.5, 0.6, f"Current LUX Price: ${price:.8f}", 
                horizontalalignment='center', fontsize=14)
        plt.text(0.5, 0.4, f"24h Change: {change:+.2f}%",
                horizontalalignment='center', fontsize=12,
                color='green' if change >= 0 else 'red')

        # Remove axes
        plt.axis('off')

        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()

        buffer.seek(0)
        print("Price display generated successfully")
        return buffer
    except Exception as e:
        print(f"Error generating price display: {str(e)}")
        return None