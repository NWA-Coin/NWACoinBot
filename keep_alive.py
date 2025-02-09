from flask import Flask
from threading import Thread
import logging

app = Flask(__name__)
logger = logging.getLogger('discord_bot')

@app.route('/')
def home():
    """Endpoint to respond to keep-alive pings"""
    return "Bot is alive!"

def run():
    """Run the Flask app in a separate thread"""
    app.run(host='0.0.0.0', port=8080)

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
