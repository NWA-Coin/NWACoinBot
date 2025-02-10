from flask import Flask
import logging
import os
from threading import Thread
import time

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    logger.info("Received request to home endpoint")
    return "Test server is running!"

@app.route('/keep-alive')
def keep_alive():
    logger.info("Received keep-alive request")
    return "Bot is alive!"

def run_server():
    """Run the Flask app"""
    try:
        # Must use PORT from environment for Replit
        port = int(os.environ.get('PORT', '8080'))
        logger.info(f"Starting unified server on port {port}")

        app.run(
            host='0.0.0.0',  # Required for external access
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.exception("Full traceback:")
        raise

if __name__ == "__main__":
    logger.info("Initializing server...")
    try:
        run_server()
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        logger.exception("Full traceback:")
        raise