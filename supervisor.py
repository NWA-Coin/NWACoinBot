import logging
import asyncio
import time
from datetime import datetime, timedelta
import signal
import sys

logger = logging.getLogger('discord_bot')

class BotSupervisor:
    def __init__(self):
        self.last_heartbeat = datetime.now()
        self.is_running = True
        self.consecutive_failures = 0
        self.MAX_FAILURES = 3
        self.HEARTBEAT_INTERVAL = 30  # seconds
        self.RESTART_COOLDOWN = 300   # 5 minutes

    async def monitor(self, bot):
        """Monitor bot's health and manage reconnection."""
        logger.info("Starting bot supervisor monitoring")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                
                if bot.is_closed():
                    logger.warning("Bot connection is closed")
                    await self.handle_disconnection(bot)
                else:
                    # Reset failure counter on successful connection
                    self.consecutive_failures = 0
                    self.last_heartbeat = datetime.now()
                    
            except Exception as e:
                logger.error(f"Error in supervisor monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def handle_disconnection(self, bot):
        """Handle bot disconnection with progressive backoff."""
        self.consecutive_failures += 1
        
        if self.consecutive_failures > self.MAX_FAILURES:
            logger.critical("Maximum consecutive failures reached!")
            await self.emergency_restart(bot)
            return

        delay = min(30 * (2 ** (self.consecutive_failures - 1)), 300)  # Max 5 minutes
        logger.info(f"Attempting reconnection in {delay} seconds (attempt {self.consecutive_failures})")
        
        await asyncio.sleep(delay)
        
        if bot.is_closed():
            try:
                await bot.close()  # Ensure clean shutdown
                await bot.start(bot.http.token, reconnect=True)
                logger.info("Bot successfully reconnected")
            except Exception as e:
                logger.error(f"Failed to reconnect: {str(e)}")

    async def emergency_restart(self, bot):
        """Emergency restart procedure for critical failures."""
        logger.warning("Initiating emergency restart procedure")
        
        try:
            await bot.close()
            logger.info("Bot connection closed for emergency restart")
            
            # Wait for cooldown period
            await asyncio.sleep(self.RESTART_COOLDOWN)
            
            # Reset failure counter
            self.consecutive_failures = 0
            
            # Attempt restart
            await bot.start(bot.http.token, reconnect=True)
            logger.info("Emergency restart completed successfully")
            
        except Exception as e:
            logger.critical(f"Emergency restart failed: {str(e)}")
            sys.exit(1)  # Exit for external process manager to handle

    def stop(self):
        """Stop the supervisor."""
        self.is_running = False
        logger.info("Bot supervisor stopped")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
