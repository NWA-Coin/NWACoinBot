import requests
from datetime import datetime
import matplotlib.pyplot as plt
import io

def fetch_lux_price_history():
    """Fetch 7-day price history for LUX token."""
    try:
        # Get 7 days of hourly data
        response = requests.get(
            "https://min-api.cryptocompare.com/data/v2/histoday",
            params={
                "fsym": "LUX",
                "tsym": "USD",
                "limit": 7  # 7 days of data
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if 'Data' in data and 'Data' in data['Data']:
                prices = []
                dates = []
                for point in data['Data']['Data']:
                    if point['close'] > 0:
                        prices.append(point['close'])
                        dates.append(datetime.fromtimestamp(point['time']))
                return dates, prices
        return None, None
    except Exception as e:
        print(f"Error fetching price data: {str(e)}")
        return None, None

def generate_price_chart():
    """Generate a price chart for LUX token."""
    try:
        dates, prices = fetch_lux_price_history()
        if not dates or not prices:
            return None

        # Create chart
        plt.figure(figsize=(10, 6))
        plt.plot(dates, prices, color='red', linewidth=2)
        
        # Customize chart
        plt.title('LUX/USD - 7 Day Price History', pad=20)
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        
        # Format y-axis
        plt.gca().yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, p: f'${x:.8f}' if x < 0.01 else f'${x:.4f}')
        )

        # Save chart
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        
        buffer.seek(0)
        return buffer
    except Exception as e:
        print(f"Error generating chart: {str(e)}")
        return None
