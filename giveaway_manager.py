import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

logger = logging.getLogger('discord_bot')

class GiveawayManager:
    def __init__(self):
        self.active_giveaway: Optional[Dict] = None
        self.participants: Set[int] = set()  # Set of discord_ids
        self.min_tokens_required = 100000  # Minimum tokens required to join
        logger.info("GiveawayManager initialized")

    def start_giveaway(self, creator_id: int, prize: str) -> bool:
        """Start a new giveaway"""
        if self.active_giveaway:
            return False
        
        self.active_giveaway = {
            'creator_id': creator_id,
            'prize': prize,
            'start_time': datetime.now(),
            'participants': set()
        }
        self.participants.clear()
        logger.info(f"New giveaway started by {creator_id} with prize: {prize}")
        return True

    def end_giveaway(self) -> Optional[Dict]:
        """End the current giveaway and return its data"""
        if not self.active_giveaway:
            return None
        
        giveaway_data = self.active_giveaway
        self.active_giveaway = None
        self.participants.clear()
        logger.info("Giveaway ended")
        return giveaway_data

    def add_participant(self, discord_id: int) -> bool:
        """Add a participant to the current giveaway"""
        if not self.active_giveaway:
            return False
        
        if discord_id in self.participants:
            return False
        
        self.participants.add(discord_id)
        self.active_giveaway['participants'].add(discord_id)
        logger.info(f"Added participant {discord_id} to giveaway")
        return True

    def get_participants(self) -> Set[int]:
        """Get the set of participant discord IDs"""
        return self.participants.copy()

    def is_active(self) -> bool:
        """Check if there's an active giveaway"""
        return self.active_giveaway is not None

    def get_active_giveaway(self) -> Optional[Dict]:
        """Get the current active giveaway data"""
        return self.active_giveaway
