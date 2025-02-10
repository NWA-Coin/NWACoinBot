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
        # Get port from environment or default to 8080
        port = int(os.getenv('PORT', 8080))
        logger.info(f"Starting Flask server on port {port}")

        # Configure Flask for production use on Replit
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False

        # Start server with threading enabled
        app.run(
            host='0.0.0.0',  # Required for external access
            port=port,
            debug=False,
            use_reloader=False,  # Disable reloader in production
            threaded=True  # Enable threading
        )
        return True
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.exception("Full traceback:")
        return False

def keep_alive():
    """Start the keep-alive server in a daemon thread"""
    try:
        # Create and start server thread
        server = Thread(target=run, daemon=True)
        server.start()

        # Give the server a moment to start
        time.sleep(2)
        logger.info("Keep-alive server started successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    if keep_alive():
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Server shutting down")
    else:
        logger.error("Failed to start server")