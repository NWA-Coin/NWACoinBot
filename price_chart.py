import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# Set up logging
logger = logging.getLogger('discord_bot')

def get_lux_price_history():
    """Get LUX price history from CoinGecko."""
    try:
        # For testing - generate mock price data showing downtrend from 0.015
        # This simulates NWA's attack on LUX from entry price
        days = 30
        initial_price = 0.015
        dates = [datetime.now() - timedelta(days=x) for x in range(days)]

        # Generate decreasing prices with more volatility
        prices = []
        current_price = initial_price
        for i in range(days):
            # Add random volatility but maintain downtrend
            change = np.random.normal(-0.15, 0.05) # Negative mean for downtrend
            current_price *= (1 + change)
            current_price = max(0.00001, current_price) # Don't go below 0
            prices.append(current_price)

        prices.reverse() # Most recent price last
        logger.info(f"Generated mock price data from {initial_price} to {prices[-1]}")
        return dates, prices

    except Exception as e:
        logger.error(f"Error fetching price history: {str(e)}")
        return None, None

def create_price_chart():
    """Create a price chart with savage roast overlay."""
    try:
        dates, prices = get_lux_price_history()
        if not dates or not prices:
            logger.error("Failed to get price data")
            return None

        # Calculate crash percentage from NWA entry
        entry_price = 0.015
        current_price = prices[-1]
        crash_percent = ((entry_price - current_price) / entry_price) * 100
        logger.info(f"Crash percentage: {crash_percent:.1f}%")

        # Create chart with dark theme
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot price line in red for the crash
        ax.plot(dates, prices, color='red', linewidth=2)

        # Customize chart
        ax.set_title(f"LUX/USD Chart\nDown {crash_percent:.1f}% since NWA Entry", 
                    color='white', size=16, pad=20)
        ax.set_xlabel("Date", color='white', size=12)
        ax.set_ylabel("Price (USD)", color='white', size=12)

        # Format y-axis with scientific notation for small numbers
        ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.8f'))

        # Add grid and customize ticks
        ax.grid(True, alpha=0.2)
        plt.xticks(rotation=45, color='white')
        plt.yticks(color='white')

        # Highlight NWA entry price
        ax.axhline(y=entry_price, color='yellow', linestyle='--', alpha=0.5,
                  label=f'NWA Entry: ${entry_price}')
        ax.legend(facecolor='#2F3136', edgecolor='white')

        # Save chart
        temp_chart = "temp_chart.png"
        plt.savefig(temp_chart, bbox_inches='tight', dpi=300, 
                   facecolor='#2F3136') # Discord-like dark theme
        plt.close()

        # Add roast text overlay
        img = Image.open(temp_chart)
        draw = ImageDraw.Draw(img)

        # Generate roast text based on crash percentage
        if crash_percent >= 90:
            roast = f"LUX DOWN {crash_percent:.1f}%! COMPLETE FUCKING DISASTER! 💀"
        elif crash_percent >= 70:
            roast = f"NWA DUMPED IT {crash_percent:.1f}%! GET REKT TINO! 🖕"
        elif crash_percent >= 50:
            roast = f"CHART'S DEAD! DOWN {crash_percent:.1f}%! NWA WINS! 🔥"
        else:
            roast = f"DUMPING {crash_percent:.1f}%! TINO'S MOM'S OF PAYS BETTER! 💸"

        # Use default font with larger size for better visibility
        font = ImageFont.load_default()

        # Position text near top of image with better contrast
        text_pos = (20, 20)
        outline_color = 'black'
        text_color = 'white'
        outline_width = 3

        # Draw text outline for better visibility
        for adj in range(-outline_width, outline_width+1):
            for adj2 in range(-outline_width, outline_width+1):
                if adj != 0 or adj2 != 0:
                    draw.text((text_pos[0]+adj, text_pos[1]+adj2), 
                            roast, font=font, fill=outline_color)

        # Draw main text
        draw.text(text_pos, roast, font=font, fill=text_color)

        # Save final image
        final_path = f"temp_meme_{datetime.now().timestamp()}.png"
        img.save(final_path, quality=95)
        logger.info(f"Successfully created price chart meme: {final_path}")
        return final_path

    except Exception as e:
        logger.error(f"Error creating price chart: {str(e)}")
        return None