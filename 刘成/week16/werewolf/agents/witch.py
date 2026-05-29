"""Witch agent."""

from typing import Optional
from werewolf.agents.base import BaseAgent
from werewolf.config import ActionType


class WitchAgent(BaseAgent):
    """Agent for witch role."""

    def night_action(self, state: dict) -> Optional[dict]:
        """Witch night action - save or poison."""
        # Check if someone was attacked tonight
        night_actions = state.get("night_actions", [])
        attacked = None
        for action in night_actions:
            if action.get("action_type") == "kill" and action.get("target_id"):
                attacked = action["target_id"]
                break

        # If first night and someone attacked, save them
        if state.get("day", 0) == 1 and attacked:
            self.memory.add_decision("save", {"target_id": attacked})
            return {
                "action_type": ActionType.SAVE,
                "target_id": attacked
            }

        # If can poison, try to find a werewolf target
        alive_players = [p for p in state.get("players", []) if p.get("is_alive")]
        for p in alive_players:
            if p["player_id"] != self.player_id:
                # Poison someone suspicious
                self.memory.add_decision("poison", {"target_id": p["player_id"]})
                return {
                    "action_type": ActionType.POISON,
                    "target_id": p["player_id"]
                }

        return None

    def get_role_name(self) -> str:
        return "witch"