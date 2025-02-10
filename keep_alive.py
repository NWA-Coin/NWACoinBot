from flask import Flask
from threading import Thread
import logging
import time

app = Flask(__name__)
logger = logging.getLogger('discord_bot')

@app.route('/')
def home():
    """Endpoint to respond to keep-alive pings"""
    logger.info("Received keep-alive ping request")
    return "Bot is alive!"

def run():
    """Run the Flask app"""
    try:
        logger.info("Starting Flask server on port 8080")
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Flask server error: {str(e)}")
        return False

def keep_alive():
    """Start the keep-alive server"""
    try:
        logger.info("Initializing keep-alive server")
        server = Thread(target=run)
        server.daemon = True
        server.start()
        logger.info("Keep-alive server thread started")
        time.sleep(2)  # Brief wait to ensure server starts
        return True
    except Exception as e:
        logger.error(f"Error starting keep-alive server: {str(e)}")
        return False

if __name__ == "__main__":
    keep_alive()
