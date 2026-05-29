"""Werewolf agent."""

from typing import Optional
from werewolf.agents.base import BaseAgent
from werewolf.config import ActionType


class WerewolfAgent(BaseAgent):
    """Agent for werewolf role."""

    def night_action(self, state: dict) -> Optional[dict]:
        """Werewolf night action - kill a target."""
        players = [p for p in state.get("players", []) if p.get("is_alive")]
        if len(players) <= 1:
            return None

        # Choose a target (prefer non-werewolf players)
        for p in players:
            if p["player_id"] != self.player_id and p.get("role") != "werewolf":
                target_id = p["player_id"]
                self.memory.add_decision("kill", {"target_id": target_id})
                return {
                    "action_type": ActionType.KILL,
                    "target_id": target_id
                }

        # Fallback
        for p in players:
            if p["player_id"] != self.player_id:
                self.memory.add_decision("kill", {"target_id": p["player_id"]})
                return {
                    "action_type": ActionType.KILL,
                    "target_id": p["player_id"]
                }

        return None

    def get_role_name(self) -> str:
        return "werewolf"