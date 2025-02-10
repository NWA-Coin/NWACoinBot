from flask import Flask
from threading import Thread
import logging
import time
import signal
import sys
import os

app = Flask(__name__)
logger = logging.getLogger('discord_bot')

# Get port from environment variable, default to 8080
PORT = int(os.getenv('PORT', 8080))

@app.route('/')
def home():
    """Simple endpoint to respond to keep-alive pings"""
    logger.info("Received health check request")
    return "Bot is alive!"

def run():
    """Run the Flask app"""
    try:
        # Use PORT from environment, important for Replit
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        return False
    return True

def keep_alive():
    """Start the keep-alive server in a daemon thread"""
    try:
        logger.info(f"Starting keep-alive server on port {PORT}")
        server_thread = Thread(target=run)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(2)  # Give the server time to start
        return True
    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if keep_alive():
        logger.info("Keep-alive server started successfully")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Server shutting down")
            sys.exit(0)
    else:
        logger.error("Failed to start keep-alive server")
        sys.exit(1)