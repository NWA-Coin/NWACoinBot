from flask import Flask
from threading import Thread
import logging
import time
import os

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot')

app = Flask(__name__)

@app.route('/')
def home():
    """Simple endpoint to respond to keep-alive pings"""
    return "Bot is alive!"

def run():
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
        return True
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.exception("Full traceback:")
        return False

def keep_alive():
    """Start the keep-alive server in a daemon thread"""
    try:
        # Create and configure server thread
        server = Thread(target=run, daemon=True, name="KeepAliveServer")
        server.start()

        # Give the server time to start
        time.sleep(2)

        # Verify server started successfully
        if server.is_alive():
            logger.info("Keep-alive server started successfully")
            return True
        else:
            logger.error("Keep-alive server failed to start")
            return False

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    if keep_alive():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Server shutting down")
    else:
        logger.error("Failed to start server")