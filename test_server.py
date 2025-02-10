import logging
import time
from flask import Flask
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_server')

app = Flask(__name__)

@app.route('/')
def home():
    """Simple endpoint to respond to keep-alive pings"""
    return "Test server is alive!"

def verify_server():
    """Test if server is responding"""
    time.sleep(2)  # Wait for server to start
    try:
        response = requests.get('http://0.0.0.0:3000')
        logger.info(f"Server test response: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Server test failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("Starting test server on port 3000...")

        # Run server in a thread so we can verify it
        from threading import Thread
        server = Thread(target=lambda: app.run(host='0.0.0.0', port=3000, debug=False, use_reloader=False))
        server.daemon = True
        server.start()

        # Verify server
        if verify_server():
            logger.info("Server started and verified successfully!")
            server.join()  # Keep server running
        else:
            logger.error("Server verification failed!")

    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")