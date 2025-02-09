from flask import Flask
from threading import Thread
import logging
import time
from datetime import datetime

app = Flask(__name__)
logger = logging.getLogger('discord_bot')

@app.route('/')
def home():
    """Endpoint to respond to keep-alive pings"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Keep-alive ping received at {current_time}")
    return "Bot is alive!"

def run():
    """Run the Flask app in a separate thread"""
    try:
        logger.info("Starting Flask server on port 8081")
        app.run(
            host='0.0.0.0',
            port=8081,
            threaded=True,
            debug=False
        )
    except Exception as e:
        logger.error(f"Flask server error: {str(e)}")
        time.sleep(5)  # Wait before retry
        run()  # Recursive retry

def keep_alive():
    """Start the keep-alive server in a background thread"""
    try:
        logger.info("Starting keep-alive server")
        server = Thread(target=run)
        server.daemon = True  # Dies when main thread dies
        server.start()
        logger.info("Keep-alive server started successfully")
    except Exception as e:
        logger.error(f"Error starting keep-alive server: {str(e)}")
        time.sleep(5)  # Wait before retry
        keep_alive()  # Recursive retry