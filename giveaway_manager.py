import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Set
import os

logger = logging.getLogger('discord_bot')

class GiveawayManager:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.active_giveaway: Optional[Dict] = None
        self.participants: Set[int] = set()  # Set of discord_ids
        self.min_tokens_required = 100000  # Minimum tokens required to join
        self.setup_database()
        logger.info("GiveawayManager initialized")

    def setup_database(self):
        """Create necessary tables if they don't exist"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Create giveaways table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS giveaways (
                            id SERIAL PRIMARY KEY,
                            creator_id BIGINT NOT NULL,
                            prize TEXT NOT NULL,
                            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            end_time TIMESTAMP,
                            is_active BOOLEAN DEFAULT TRUE,
                            winner_id BIGINT
                        )
                    """)

                    # Create giveaway_participants table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS giveaway_participants (
                            id SERIAL PRIMARY KEY,
                            giveaway_id INTEGER REFERENCES giveaways(id),
                            discord_id BIGINT NOT NULL,
                            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(giveaway_id, discord_id)
                        )
                    """)
                    conn.commit()
                    logger.info("Giveaway database tables created successfully")
        except Exception as e:
            logger.error(f"Database setup error: {str(e)}")
            raise

    def start_giveaway(self, creator_id: int, prize: str) -> bool:
        """Start a new giveaway"""
        try:
            # Check if there's already an active giveaway
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM giveaways 
                        WHERE is_active = TRUE
                    """)
                    if cur.fetchone():
                        return False

                    # Create new giveaway
                    cur.execute("""
                        INSERT INTO giveaways (creator_id, prize)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (creator_id, prize))
                    giveaway_id = cur.fetchone()[0]
                    conn.commit()

                    self.active_giveaway = {
                        'id': giveaway_id,
                        'creator_id': creator_id,
                        'prize': prize,
                        'start_time': datetime.now(),
                        'participants': set()
                    }
                    self.participants.clear()
                    logger.info(f"New giveaway started by {creator_id} with prize: {prize}")
                    return True
        except Exception as e:
            logger.error(f"Error starting giveaway: {str(e)}")
            return False

    def end_giveaway(self) -> Optional[Dict]:
        """End the current giveaway and return its data"""
        try:
            if not self.active_giveaway:
                return None

            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Mark giveaway as ended
                    cur.execute("""
                        UPDATE giveaways 
                        SET is_active = FALSE,
                            end_time = NOW()
                        WHERE id = %s AND is_active = TRUE
                        RETURNING id
                    """, (self.active_giveaway['id'],))
                    conn.commit()

            giveaway_data = self.active_giveaway
            self.active_giveaway = None
            self.participants.clear()
            logger.info("Giveaway ended")
            return giveaway_data

        except Exception as e:
            logger.error(f"Error ending giveaway: {str(e)}")
            return None

    def add_participant(self, discord_id: int) -> bool:
        """Add a participant to the current giveaway"""
        try:
            if not self.active_giveaway:
                return False

            if discord_id in self.participants:
                return False

            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Add participant to database
                    cur.execute("""
                        INSERT INTO giveaway_participants (giveaway_id, discord_id)
                        VALUES (%s, %s)
                        ON CONFLICT (giveaway_id, discord_id) DO NOTHING
                        RETURNING id
                    """, (self.active_giveaway['id'], discord_id))

                    if cur.fetchone():
                        conn.commit()
                        self.participants.add(discord_id)
                        self.active_giveaway['participants'].add(discord_id)
                        logger.info(f"Added participant {discord_id} to giveaway")
                        return True
                    return False

        except Exception as e:
            logger.error(f"Error adding participant: {str(e)}")
            return False

    def get_participants(self) -> Set[int]:
        """Get the set of participant discord IDs"""
        if not self.active_giveaway:
            return set()
        return self.participants.copy()

    def is_active(self) -> bool:
        """Check if there's an active giveaway"""
        return self.active_giveaway is not None

    def get_active_giveaway(self) -> Optional[Dict]:
        """Get the current active giveaway data"""
        return self.active_giveaway

    def set_winner(self, giveaway_id: int, winner_id: int) -> bool:
        """Set the winner for a giveaway"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE giveaways 
                        SET winner_id = %s
                        WHERE id = %s AND is_active = FALSE
                        RETURNING id
                    """, (winner_id, giveaway_id))
                    if cur.fetchone():
                        conn.commit()
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error setting winner: {str(e)}")
            return False