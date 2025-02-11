import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, Tuple, Dict
from datetime import datetime

# Set up logging
logger = logging.getLogger('discord_bot')

# Constants for token configuration 
TOKEN_CONTRACT = "J9RZefdNW9eTCiVPLtke5rashEUGeVaXLk7iWFTupump"  # NWADEV token contract
MIN_HOLDING_AMOUNT = 100000  # Minimum tokens required for airdrop
AIRDROP_AMOUNT = 100000  # Amount of tokens to airdrop to eligible users

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
        """Get token balance using Solana Web3.js implementation"""
        try:
            if not contract_address:
                contract_address = TOKEN_CONTRACT

            # Initialize balance checker
            checker = TokenBalanceChecker()
            balance = await checker.get_balance(wallet_address, contract_address)

            if balance is not None:
                # Convert to integer as we store whole token amounts
                return int(balance)

            return None

        except Exception as e:
            logger.error(f"Error in get_token_balance: {str(e)}")
            logger.exception("Full traceback:")
            return None

    async def update_wallet_balance(self, discord_id: int) -> bool:
        """Update wallet's token balance
        Returns success status"""
        try:
            # Get current balance
            success, balance = await self.force_balance_update(discord_id)
            if not success or balance is None:
                return False

            # Update balance in database
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
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
                    """, (int(balance), int(balance), MIN_HOLDING_AMOUNT, discord_id))

                    result = cur.fetchone()
                    conn.commit()

                    if result:
                        logger.info(f"Updated balance for {result[0]} to {balance} tokens")
                        return True
                    else:
                        logger.warning(f"No verified wallet found for discord_id {discord_id}")
                        return False

        except Exception as e:
            logger.error(f"Error updating token balance: {str(e)}")
            logger.exception("Full traceback:")
            return False

    async def force_balance_update(self, discord_id: int, contract_address: Optional[str] = None) -> Tuple[bool, Optional[int]]:
        """Force update wallet's token balance
        Returns (success, balance)"""
        try:
            # Get user's wallet
            wallet = await self.get_user_wallet(discord_id)
            if not wallet:
                logger.warning(f"No verified wallet found for discord_id {discord_id}")
                return False, None

            # Use the specified contract or default NWA token
            token_contract = contract_address if contract_address else TOKEN_CONTRACT

            # Initialize balance checker
            checker = TokenBalanceChecker()
            balance = await checker.get_balance(wallet['wallet_address'], token_contract)

            if balance is None:
                logger.error(f"Failed to get balance for wallet {wallet['wallet_address']}")
                return False, None

            # Only update stored balance if checking NWA token
            if not contract_address:
                # Store the new balance
                if not await self.update_token_balance(discord_id):
                    logger.error("Failed to update stored balance in database")
                    return False, None

            return True, int(balance)  # Return integer token amount

        except Exception as e:
            logger.error(f"Error in force_balance_update: {str(e)}")
            logger.exception("Full traceback:")
            return False, None

    async def check_airdrop_eligibility(self, discord_id: int) -> Tuple[bool, Optional[float], bool]:
        """Check if a user is eligible for airdrop based on token holdings
        Returns (success, balance, eligible)"""
        try:
            # Force update balance to get current holdings
            success, balance = await self.force_balance_update(discord_id)
            if not success or balance is None:
                return False, None, False

            # Check if balance meets minimum requirement
            eligible = balance >= MIN_HOLDING_AMOUNT

            logger.info(
                f"Airdrop eligibility check for {discord_id}: "
                f"balance={balance}, eligible={eligible}"
            )

            return True, float(balance), eligible

        except Exception as e:
            logger.error(f"Error checking airdrop eligibility: {str(e)}")
            logger.exception("Full traceback:")
            return False, None, False

    async def link_wallet(self, discord_id: int, wallet_address: str) -> tuple[bool, str]:
        """Link a Solana wallet to a Discord user
        Returns (success, message)"""
        try:
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
                            verification_code = os.urandom(6).hex()
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
                        verification_code = os.urandom(6).hex()
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
        """Verify a wallet link using the verification code
        Returns (success, message)"""
        try:
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

                    # Mark as verified
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

    async def update_token_balance(self, discord_id: int, new_balance: float = None) -> bool:
        """Update the token balance and check airdrop eligibility"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Update balance and check eligibility
                    if new_balance is None:
                        success, new_balance = await self.force_balance_update(discord_id)
                        if not success:
                            return False

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

class TokenBalanceChecker: # Assuming this class is defined elsewhere and handles balance retrieval.
    async def get_balance(self, wallet_address, contract_address):
        #Implementation for getting balance using Solana Web3.js.  This is a placeholder.
        return 100000 #Example balance.  Replace with actual implementation.
        pass