import asyncio
import logging
import json
import subprocess
from typing import Optional, Dict, Any

logger = logging.getLogger('discord_bot')

class TokenBalanceChecker:
    def __init__(self):
        self.node_process = None
        logger.info("TokenBalanceChecker initialized")

    async def get_balance(self, wallet_address: str, token_address: str) -> Optional[float]:
        """
        Get token balance using Node.js Web3 implementation
        Returns the adjusted token balance or None if error
        """
        try:
            # Run the Node.js script with improved error handling
            cmd = [
                'node', '-e', 
                f"""
                const {{ getTokenBalance }} = require('./token_checker.js');
                getTokenBalance('{wallet_address}', '{token_address}')
                    .then(result => {{
                        console.log(JSON.stringify(result));
                        process.exit(0);
                    }})
                    .catch(err => {{
                        console.error(JSON.stringify({{
                            error: err.message,
                            stack: err.stack
                        }}));
                        process.exit(1);
                    }});
                """
            ]

            logger.info(f"Checking balance for wallet {wallet_address} and token {token_address}")

            # Execute Node.js process with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                # Add 30-second timeout for balance checking
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.error("Balance check timed out after 30 seconds")
                if process.returncode is None:
                    process.terminate()
                return None

            if process.returncode != 0:
                error_data = stderr.decode().strip()
                try:
                    # Try to parse error as JSON
                    error_json = json.loads(error_data)
                    logger.error(f"Node.js error: {error_json.get('error', 'Unknown error')}")
                    if error_json.get('stack'):
                        logger.debug(f"Error stack trace: {error_json['stack']}")
                except json.JSONDecodeError:
                    logger.error(f"Raw Node.js error: {error_data}")
                return None

            # Parse the JSON response
            response_data = stdout.decode().strip()
            try:
                result = json.loads(response_data)
                adjusted_balance = float(result['adjusted'])

                logger.info(
                    f"Balance retrieved: {adjusted_balance} "
                    f"(raw: {result['raw']}, decimals: {result['decimals']})"
                )
                return adjusted_balance

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse balance response: {str(e)}")
                logger.debug(f"Raw response: {response_data}")
                return None

        except Exception as e:
            logger.error(f"Error in get_balance: {str(e)}")
            logger.exception("Full traceback:")
            return None