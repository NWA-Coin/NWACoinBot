import os
import logging
import asyncio
import base58
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

# Set up logging
logger = logging.getLogger('discord_bot')

class WalletManager:
    def __init__(self):
        """Initialize database connection"""
        self.db_url = os.getenv('DATABASE_URL')
        self.setup_database()

    def setup_database(self):
        """Create necessary tables if they don't exist"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Create wallet_links table with airdrop tracking
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS wallet_links (
                            id SERIAL PRIMARY KEY,
                            discord_id BIGINT NOT NULL UNIQUE,
                            wallet_address TEXT NOT NULL UNIQUE,
                            verified BOOLEAN DEFAULT FALSE,
                            verification_code TEXT,
                            airdrop_claimed BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Database setup error: {str(e)}")
            raise

    async def link_wallet(self, discord_id: int, wallet_address: str) -> tuple[bool, str]:
        """
        Link a single NWA wallet for a Discord user
        Returns (success, message)
        """
        try:
            # Enhanced Solana address validation
            try:
                # Solana addresses are base58 encoded and 32 bytes (decoded)
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
                            return False, "You already have a verified NWA wallet linked!"
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
            # Input validation
            if not verification_code or len(verification_code) > 32:
                return False, "Invalid verification code format"

            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Add timeout for verification (24 hours)
                    cur.execute("""
                        SELECT * FROM wallet_links 
                        WHERE discord_id = %s 
                        AND verification_code = %s 
                        AND verified = FALSE
                        AND created_at > NOW() - INTERVAL '24 hours'
                    """, (discord_id, verification_code))
                    link = cur.fetchone()

                    if not link:
                        return False, "Invalid or expired verification code"

                    # Mark as verified
                    cur.execute("""
                        UPDATE wallet_links 
                        SET verified = TRUE, verification_code = NULL 
                        WHERE discord_id = %s AND wallet_address = %s
                    """, (discord_id, link['wallet_address']))
                    conn.commit()

                    return True, f"Successfully verified your NWA wallet: {link['wallet_address']}"

        except Exception as e:
            logger.error(f"Error verifying wallet: {str(e)}")
            return False, "An error occurred while verifying the wallet"

    async def get_user_wallet(self, discord_id: int) -> Optional[dict]:
        """Get the verified wallet linked to a Discord user"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT wallet_address, created_at, airdrop_claimed
                        FROM wallet_links 
                        WHERE discord_id = %s AND verified = TRUE
                    """, (discord_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting user wallet: {str(e)}")
            return None

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