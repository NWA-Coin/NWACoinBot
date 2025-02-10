from flask import Flask
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    logger.info("Received request to home endpoint")
    return "Test server is running!"

if __name__ == "__main__":
    try:
        port = int(os.getenv('PORT', 8081))  # Changed default port to 8081
        logger.info(f"Starting test server on port {port}")

        app.run(
            host='0.0.0.0',
            port=port,
            debug=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.exception("Full traceback:")