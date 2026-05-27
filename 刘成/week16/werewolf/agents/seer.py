"""Seer agent."""

from typing import Optional
from werewolf.agents.base import BaseAgent
from werewolf.config import ActionType


class SeerAgent(BaseAgent):
    """Agent for seer role."""

    def night_action(self, state: dict) -> Optional[dict]:
        """Seer night action - check a player's identity."""
        # Get previous checks
        checked = state.get("seer_checks", {})
        alive_players = [p for p in state.get("players", []) if p.get("is_alive")]

        # Find an unchecked player to verify
        for p in alive_players:
            if p["player_id"] != self.player_id and str(p["player_id"]) not in checked:
                self.memory.add_decision("check", {"target_id": p["player_id"]})
                return {
                    "action_type": ActionType.CHECK,
                    "target_id": p["player_id"]
                }

        # All checked or no one left
        return None

    def get_role_name(self) -> str:
        return "seer"