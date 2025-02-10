async def generate_meme(timeframe="1hr"):
    """Generate a price chart meme."""
    try:
        logger.info(f"Starting meme generation with timeframe {timeframe}")

        # Generate price chart and get price data
        chart_path, timestamps, prices = await create_price_chart(timeframe)
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
