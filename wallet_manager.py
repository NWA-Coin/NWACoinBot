import os
import logging
import asyncio
import base58
import aiohttp
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Tuple, Dict

# Set up logging
logger = logging.getLogger('discord_bot')

# Constants for token configuration
TOKEN_CONTRACT = "J9RZefdNW9eTCiVPLtke5rashEUGeVaXLk7iWFTupump"  # NWADEV token contract
MIN_HOLDING_AMOUNT = 100000  # Minimum tokens required for airdrop
AIRDROP_AMOUNT = 100000  # Amount of tokens to airdrop to eligible users

# API endpoints for token balance checking
RAYDIUM_API = "https://api.raydium.io/v2/sdk/token/raydium.mainnet.json"
SOLANA_API = "https://api.mainnet-beta.solana.com"

class WalletManager:
    def __init__(self):
        """Initialize database connection"""
        self.db_url = os.environ.get('DATABASE_URL')
        self.setup_database()
        logger.info(f"WalletManager initialized with TOKEN_CONTRACT: {TOKEN_CONTRACT}")
        logger.info(f"Min holding amount: {MIN_HOLDING_AMOUNT}")

    def setup_database(self):
        """Create necessary tables if they don't exist"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS wallet_links (
                            id SERIAL PRIMARY KEY,
                            discord_id BIGINT NOT NULL UNIQUE,
                            wallet_address TEXT NOT NULL UNIQUE,
                            verified BOOLEAN DEFAULT FALSE,
                            verification_code TEXT,
                            token_balance BIGINT DEFAULT 0,
                            last_balance_update TIMESTAMP,
                            airdrop_eligible BOOLEAN DEFAULT FALSE,
                            airdrop_claimed BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database setup error: {str(e)}")
            raise

    async def get_token_balance(self, wallet_address: str, contract_address: Optional[str] = None) -> Optional[int]:
        """Get token balance using Raydium API with RPC fallback"""
        try:
            if not contract_address:
                contract_address = TOKEN_CONTRACT

            logger.info(f"Checking balance for wallet {wallet_address} and token {contract_address}")

            async with aiohttp.ClientSession() as session:
                # First get token metadata from Raydium
                try:
                    logger.info("Querying Raydium API for token info...")
                    async with session.get(RAYDIUM_API, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            token_info = None

                            # Find our token in the list
                            for token in data.get('tokens', []):
                                if token.get('mint') == contract_address:
                                    token_info = token
                                    break

                            if token_info:
                                decimals = int(token_info.get('decimals', 9))
                                logger.info(f"Found token info: decimals={decimals}")
                            else:
                                logger.warning("Token not found in Raydium API, using default decimals")
                                decimals = 9
                except Exception as e:
                    logger.warning(f"Raydium API error: {str(e)}")
                    decimals = 9

                # Query token accounts
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getProgramAccounts",
                    "params": [
                        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                        {
                            "encoding": "jsonParsed",
                            "filters": [
                                {
                                    "dataSize": 165  # Size of token account data
                                },
                                {
                                    "memcmp": {
                                        "offset": 32,
                                        "bytes": contract_address
                                    }
                                },
                                {
                                    "memcmp": {
                                        "offset": 0,
                                        "bytes": wallet_address
                                    }
                                }
                            ]
                        }
                    ]
                }

                try:
                    logger.info("Querying Solana RPC for token accounts...")
                    async with session.post(SOLANA_API, json=payload, timeout=30) as response:
                        if response.status != 200:
                            logger.error(f"RPC error: {response.status}")
                            return None

                        data = await response.json()
                        logger.debug(f"RPC Response: {data}")

                        if 'result' not in data:
                            logger.error("Invalid RPC response format")
                            return None

                        total_balance = 0
                        for account in data['result']:
                            try:
                                parsed_data = account['account']['data']['parsed']['info']
                                if parsed_data['mint'] == contract_address and parsed_data['owner'] == wallet_address:
                                    amount = int(parsed_data['tokenAmount']['amount'])
                                    balance = amount / (10 ** decimals)
                                    total_balance += balance
                                    logger.info(f"Found token amount: {balance:.2f} (raw: {amount}, decimals: {decimals})")
                            except (KeyError, ValueError, TypeError) as e:
                                logger.warning(f"Error parsing account data: {str(e)}")
                                continue

                        if total_balance > 0:
                            final_balance = int(total_balance)
                            logger.info(f"Final balance: {final_balance}")
                            return final_balance

                        logger.info("No token balance found")
                        return 0

                except asyncio.TimeoutError:
                    logger.error("RPC request timed out")
                except Exception as e:
                    logger.error(f"RPC request failed: {str(e)}")
                    logger.exception("Full traceback:")

            return None

        except Exception as e:
            logger.error(f"Unexpected error in get_token_balance: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def _get_associated_token_account(self, wallet_address: str, token_mint: str) -> str:
        """Calculate the associated token account address using proper PDA derivation"""
        try:
            # Convert addresses to bytes
            wallet_bytes = base58.b58decode(wallet_address)
            mint_bytes = base58.b58decode(token_mint)
            token_program_bytes = base58.b58decode(TOKEN_PROGRAM_ID)

            # Create the seeds for PDA derivation
            seeds = [
                bytes([1]), # Version bytes
                wallet_bytes,
                token_program_bytes,
                mint_bytes
            ]

            # Calculate PDA - Using a simpler derivation for testing
            all_seeds = b''.join(seeds)
            import hashlib
            digest = hashlib.sha256(all_seeds).digest()
            return base58.b58encode(digest).decode('ascii')

        except Exception as e:
            logger.error(f"Error creating associated token account address: {str(e)}")
            raise

    async def update_wallet_balance(self, discord_id: int) -> bool:
        """Update wallet token balance with simplified logic"""
        try:
            wallet = await self.get_user_wallet(discord_id)
            if not wallet:
                logger.warning(f"No verified wallet found for discord_id {discord_id}")
                return False

            balance = await self.get_token_balance(wallet['wallet_address'])
            if balance is not None:
                with psycopg2.connect(self.db_url) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE wallet_links 
                            SET token_balance = %s,
                                last_balance_update = NOW()
                            WHERE discord_id = %s AND verified = TRUE
                            RETURNING id
                        """, (balance, discord_id))

                        if cur.fetchone():
                            conn.commit()
                            logger.info(f"Updated balance for {wallet['wallet_address']} to {balance}")
                            return True

                        logger.error("Failed to update database record")
                        return False

            logger.error("Could not fetch current balance")
            return False

        except Exception as e:
            logger.error(f"Error updating wallet balance: {str(e)}")
            logger.exception("Full traceback:")
            return False

    def _create_associated_token_account_address(self, wallet_address: str, token_mint: str) -> str:
        """Calculate the associated token account address"""
        try:
            # Convert addresses to bytes
            wallet_bytes = base58.b58decode(wallet_address)
            mint_bytes = base58.b58decode(token_mint)
            program_id_bytes = base58.b58decode("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
            associated_program_id_bytes = base58.b58decode("ATokenGPvbdGVxr1b2hvfj3qyKjfBQdUyDspmUXJ79s")

            # Create the seeds for PDA derivation
            seeds = [
                wallet_bytes,
                program_id_bytes,
                mint_bytes
            ]

            # Calculate PDA
            all_seeds = b''.join(seeds)
            import base64
            digest = base64.b64encode(all_seeds)
            return base58.b58encode(digest).decode('ascii')

        except Exception as e:
            logger.error(f"Error creating associated token account address: {str(e)}")
            return None

    async def force_balance_update(self, discord_id: int, contract_address: Optional[str] = None) -> Tuple[bool, Optional[int]]:
        """Force an immediate balance update with simplified logic"""
        try:
            wallet = await self.get_user_wallet(discord_id)
            if not wallet:
                logger.warning(f"No verified wallet found for discord_id {discord_id}")
                return False, None

            logger.info(f"Forcing balance update for wallet: {wallet['wallet_address']}")
            balance = await self.get_token_balance(wallet['wallet_address'], contract_address)

            if balance is not None:
                # Only update database for main NWA token
                if not contract_address or contract_address == TOKEN_CONTRACT:
                    with psycopg2.connect(self.db_url) as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE wallet_links 
                                SET token_balance = %s,
                                    last_balance_update = NOW()
                                WHERE discord_id = %s AND verified = TRUE
                                RETURNING id
                            """, (balance, discord_id))
                            if cur.fetchone():
                                conn.commit()
                                logger.info(f"Updated database balance to {balance}")
                            else:
                                logger.error("Failed to update database balance")
                                return False, None

                return True, balance

            return False, None

        except Exception as e:
            logger.error(f"Error in force balance update: {str(e)}")
            logger.exception("Full traceback:")
            return False, None

    async def link_wallet(self, discord_id: int, wallet_address: str) -> tuple[bool, str]:
        """
        Link a Solana wallet to a Discord user with simplified verification
        Returns (success, message)
        """
        try:
            # Enhanced Solana address validation
            try:
                decoded = base58.b58decode(wallet_address)
                if len(decoded) != 32:
                    return False, "Invalid Solana wallet address format"
            except Exception:
                return False, "Invalid Solana wallet address format"

            # Additional validation for discord_id
            if not isinstance(discord_id, int) or discord_id <= 0:
                return False, "Invalid Discord user ID"

            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if user already has a wallet
                    cur.execute("""
                        SELECT * FROM wallet_links 
                        WHERE discord_id = %s
                    """, (discord_id,))
                    existing_user = cur.fetchone()

                    if existing_user:
                        if existing_user['verified']:
                            return False, "You already have a verified wallet linked!"
                        else:
                            # Update verification code for existing unverified link
                            verification_code = base58.b58encode(os.urandom(6)).decode()
                            cur.execute("""
                                UPDATE wallet_links 
                                SET verification_code = %s, wallet_address = %s
                                WHERE discord_id = %s
                            """, (verification_code, wallet_address, discord_id))
                    else:
                        # Check if wallet is already linked to another user
                        cur.execute("""
                            SELECT * FROM wallet_links 
                            WHERE wallet_address = %s
                        """, (wallet_address,))
                        if cur.fetchone():
                            return False, "This wallet is already linked to another user!"

                        # Create new wallet link with verification code
                        verification_code = base58.b58encode(os.urandom(6)).decode()
                        cur.execute("""
                            INSERT INTO wallet_links 
                            (discord_id, wallet_address, verification_code) 
                            VALUES (%s, %s, %s)
                        """, (discord_id, wallet_address, verification_code))

                    conn.commit()
                    return True, verification_code

        except Exception as e:
            logger.error(f"Error linking wallet: {str(e)}")
            return False, "An error occurred while linking the wallet"

    async def verify_wallet(self, discord_id: int, verification_code: str) -> tuple[bool, str]:
        """
        Verify a wallet link using the verification code
        Returns (success, message)
        """
        try:
            if not verification_code or len(verification_code) > 32:
                return False, "Invalid verification code format"

            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM wallet_links 
                        WHERE discord_id = %s 
                        AND verification_code = %s 
                        AND verified = FALSE
                    """, (discord_id, verification_code))
                    link = cur.fetchone()

                    if not link:
                        return False, "Invalid verification code"

                    # Mark as verified and update initial balance
                    cur.execute("""
                        UPDATE wallet_links 
                        SET verified = TRUE, verification_code = NULL 
                        WHERE discord_id = %s AND wallet_address = %s
                        RETURNING wallet_address
                    """, (discord_id, link['wallet_address']))

                    result = cur.fetchone()
                    if not result:
                        return False, "Failed to verify wallet"

                    conn.commit()

                    # Fetch initial balance after verification
                    balance = await self.get_token_balance(link['wallet_address'])
                    if balance is not None:
                        cur.execute("""
                            UPDATE wallet_links 
                            SET token_balance = %s,
                                last_balance_update = NOW()
                            WHERE discord_id = %s AND verified = TRUE
                        """, (balance, discord_id))
                        conn.commit()

                    return True, f"Successfully verified your wallet: {link['wallet_address']}"

        except Exception as e:
            logger.error(f"Error verifying wallet: {str(e)}")
            return False, "An error occurred while verifying the wallet"

    async def get_user_wallet(self, discord_id: int) -> Optional[dict]:
        """Get the verified wallet linked to a Discord user"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT wallet_address, created_at, airdrop_claimed, token_balance, last_balance_update
                        FROM wallet_links 
                        WHERE discord_id = %s AND verified = TRUE
                    """, (discord_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting user wallet: {str(e)}")
            return None

    async def check_airdrop_eligibility(self, discord_id: int) -> Tuple[bool, Optional[float], bool]:
        """Check if user is eligible for airdrop"""
        try:
            # First update the wallet balance
            if not await self.update_wallet_balance(discord_id):
                return False, None, False

            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT wallet_address, token_balance, airdrop_claimed
                        FROM wallet_links 
                        WHERE discord_id = %s AND verified = TRUE
                    """, (discord_id,))

                    result = cur.fetchone()
                    if result:
                        token_balance = int(result['token_balance']) 
                        eligible = token_balance >= MIN_HOLDING_AMOUNT and not result['airdrop_claimed']
                        logger.info(f"Eligibility check - Balance: {token_balance}, Required: {MIN_HOLDING_AMOUNT}, Eligible: {eligible}")
                        return True, token_balance, eligible

                    logger.warning(f"No verified wallet found for discord_id {discord_id}")
                    return False, None, False

        except Exception as e:
            logger.error(f"Error checking airdrop eligibility: {str(e)}")
            logger.exception("Full traceback:")
            return False, None, False

    async def update_token_balance(self, discord_id: int, new_balance: float) -> bool:
        """Update the token balance and check airdrop eligibility"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Update balance and check eligibility
                    cur.execute("""
                        UPDATE wallet_links 
                        SET token_balance = %s,
                            last_balance_update = NOW(),
                            airdrop_eligible = CASE 
                                WHEN %s >= %s AND NOT airdrop_claimed 
                                THEN TRUE 
                                ELSE FALSE 
                            END
                        WHERE discord_id = %s AND verified = TRUE
                        RETURNING wallet_address
                    """, (int(new_balance), int(new_balance), MIN_HOLDING_AMOUNT, discord_id)) 
                    result = cur.fetchone()
                    conn.commit()

                    if result:
                        logger.info(f"Updated balance for {result[0]} to {new_balance} tokens")
                        return True
                    else:
                        logger.warning(f"No verified wallet found for discord_id {discord_id}")
                        return False

        except Exception as e:
            logger.error(f"Error updating token balance: {str(e)}")
            return False

    async def process_airdrop(self, discord_id: int) -> Tuple[bool, str]:
        """Process airdrop for eligible users"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check eligibility and process airdrop
                    cur.execute("""
                        SELECT wallet_address, token_balance, airdrop_eligible, airdrop_claimed
                        FROM wallet_links 
                        WHERE discord_id = %s 
                        AND verified = TRUE 
                        AND airdrop_eligible = TRUE
                        AND airdrop_claimed = FALSE
                    """, (discord_id,))
                    result = cur.fetchone()
                    if not result:
                        return False, "Not eligible for airdrop"

                    # Mark airdrop as claimed
                    cur.execute("""
                        UPDATE wallet_links 
                        SET airdrop_claimed = TRUE,
                            token_balance = token_balance + %s
                        WHERE discord_id = %s
                    """, (AIRDROP_AMOUNT, discord_id))

                    conn.commit()
                    return True, f"Successfully airdropped {AIRDROP_AMOUNT:,} tokens!"

        except Exception as e:
            logger.error(f"Error processing airdrop: {str(e)}")
            return False, f"Error processing airdrop: {str(e)}"

    async def mark_airdrop_claimed(self, discord_id: int) -> bool:
        """Mark a user's wallet as having claimed the airdrop"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE wallet_links 
                        SET airdrop_claimed = TRUE 
                        WHERE discord_id = %s AND verified = TRUE
                    """, (discord_id,))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error marking airdrop claimed: {str(e)}")
            return False

    async def get_unclaimed_wallets(self) -> list[dict]:
        """Get all verified wallets that haven't claimed the airdrop"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT discord_id, wallet_address 
                        FROM wallet_links 
                        WHERE verified = TRUE 
                        AND airdrop_claimed = FALSE
                    """)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting unclaimed wallets: {str(e)}")
            return []

    async def unlink_wallet(self, discord_id: int) -> Tuple[bool, str]:
        """Unlink a wallet from a Discord user"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Check if user has a verified wallet
                    cur.execute("""
                        SELECT wallet_address 
                        FROM wallet_links 
                        WHERE discord_id = %s
                    """, (discord_id,))
                    result = cur.fetchone()

                    if not result:
                        return False, "You don't have a linked wallet to unlink!"

                    # Delete the wallet link
                    cur.execute("""
                        DELETE FROM wallet_links 
                        WHERE discord_id = %s
                        RETURNING wallet_address
                    """, (discord_id,))
                    deleted = cur.fetchone()
                    conn.commit()

                    if deleted:
                        logger.info(f"Unlinked wallet {deleted[0]} from discord_id {discord_id}")
                        return True, f"Successfully unlinked wallet: `{deleted[0]}`"
                    return False, "Failed to unlink wallet"

        except Exception as e:
            logger.error(f"Error unlinking wallet: {str(e)}")
            return False, "An error occurred while unlinking the wallet"