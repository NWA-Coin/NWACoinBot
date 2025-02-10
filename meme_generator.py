import os
import logging
from datetime import datetime
from PIL import Image
from price_chart import create_price_chart

# Set up logging
logger = logging.getLogger('discord_bot')

async def generate_meme(timeframe="1hr", token_id="lux-token", token_symbol="LUX", entry_price=None, show_takeover_line=False):
    """Generate a price chart meme.

    Args:
        timeframe (str): Time period for chart (1hr, 24hr, 7d, 1m, 3m)
        token_id (str): CoinGecko token ID or contract address
        token_symbol (str): Token symbol for display
        entry_price (float, optional): Entry price for takeover line
        show_takeover_line (bool): Whether to show NWA takeover line
    """
    try:
        logger.info(f"Starting meme generation for {token_symbol} with timeframe {timeframe}")

        # Only use entry_price if show_takeover_line is True
        chart_entry_price = entry_price if show_takeover_line else None

        # Generate price chart and get price data
        chart_path, timestamps, prices = await create_price_chart(
            timeframe=timeframe,
            token_id=token_id,
            token_symbol=token_symbol,
            entry_price=chart_entry_price,
            show_takeover_line=show_takeover_line
        )

        if not chart_path or not timestamps or not prices:
            logger.error("Failed to generate chart")
            raise Exception("Chart generation failed")

        # Use the chart directly without adding any additional text
        final_path = f"price_meme_{int(datetime.now().timestamp())}.png"

        # Just copy the chart to the final path
        try:
            with Image.open(chart_path) as img:
                img.save(final_path, quality=95)
            logger.info(f"Successfully saved final meme: {final_path}")
        except Exception as e:
            logger.error(f"Error saving meme: {str(e)}")
            return None

        # Clean up temporary files
        try:
            os.remove(chart_path)
            logger.info(f"Cleaned up chart: {chart_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up chart: {str(e)}")

        return final_path

    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        logger.exception("Full traceback:")
        return None