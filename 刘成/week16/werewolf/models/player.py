"""Player models."""

from enum import Enum
from pydantic import BaseModel, Field


class Player(BaseModel):
    """Player model."""
    player_id: int
    name: str
    role: str
    is_alive: bool = True
    is_ai: bool = True
    # For werewolves to know their teammates (not visible to others)
    secret_role: str = ""

    def get_public_info(self) -> dict:
        """Get public information about the player."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role if not self.is_alive else "unknown",
            "is_alive": self.is_alive,
        }

    def get_known_info(self, viewer_id: int) -> dict:
        """Get information visible to a specific viewer."""
        info = self.get_public_info()
        # If the player is dead, reveal their role
        if not self.is_alive:
            info["role"] = self.role
        return info


class Camp:
    """Camp constants for win conditions."""
    GOOD = "good"
    WEREWOLF = "werewolf"
    NEUTRAL = "neutral"