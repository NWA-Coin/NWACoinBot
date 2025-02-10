from flask import Flask
from threading import Thread
import logging
import time
import signal
import sys
import socket

app = Flask(__name__)
logger = logging.getLogger('discord_bot')

# Configuration
PORTS = [8080, 8000, 5000]  # Try multiple ports
RETRY_DELAY = 5  # seconds between retries
MAX_RETRIES = 3  # maximum number of retry attempts
STARTUP_TIMEOUT = 30  # seconds to wait for server to start

@app.route('/')
def home():
    """Endpoint to respond to keep-alive pings"""
    logger.info("Health check request received")
    return "Bot is alive!"

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            logger.info(f"Port {port} is available")
            return False
        except socket.error:
            logger.warning(f"Port {port} is in use")
            return True

def find_available_port():
    """Find first available port from the list"""
    logger.info("Searching for available port...")
    for port in PORTS:
        if not is_port_in_use(port):
            logger.info(f"Selected port {port}")
            return port
    logger.error("No available ports found")
    return None

def verify_server_running(port):
    """Verify that the server is actually running and responding"""
    import requests
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = requests.get(f'http://0.0.0.0:{port}/')
            if response.status_code == 200:
                logger.info(f"Server verified running on port {port}")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False

def run():
    """Run the Flask app with enhanced reliability and port selection"""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            port = find_available_port()
            if not port:
                logger.error("No available ports found")
                time.sleep(RETRY_DELAY)
                retries += 1
                continue

            logger.info(f"Starting Flask server on port {port}")
            server_thread = Thread(target=app.run, kwargs={
                'host': '0.0.0.0',
                'port': port,
                'debug': False,
                'use_reloader': False,
                'threaded': True
            })
            server_thread.daemon = True
            server_thread.start()

            # Verify server started successfully
            if verify_server_running(port):
                logger.info("Server startup verified successfully")
                return True

            logger.error("Server failed to start properly")
            retries += 1

        except Exception as e:
            logger.error(f"Flask server error: {str(e)}")
            retries += 1
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Maximum retries reached")
                return False

    return False

def keep_alive():
    """Start the keep-alive server in a persistent daemon thread"""
    try:
        logger.info("Initializing keep-alive server")

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            sys.exit(0)

        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Start server
        if not run():
            logger.error("Failed to start keep-alive server")
            return False

        logger.info("Keep-alive server started successfully")
        return True

    except Exception as e:
        logger.error(f"Error starting keep-alive server: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    keep_alive()
    # Keep the main thread alive with health checks
    try:
        while True:
            logger.info("Keep-alive server health check")
            time.sleep(60)  # Health check every minute
    except KeyboardInterrupt:
        logger.info("Keep-alive server shutting down")
        sys.exit(0)