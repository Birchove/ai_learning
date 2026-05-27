"""Guard agent."""

from typing import Optional
from werewolf.agents.base import BaseAgent
from werewolf.config import ActionType


class GuardAgent(BaseAgent):
    """Agent for guard role."""

    def night_action(self, state: dict) -> Optional[dict]:
        """Guard night action - protect a player."""
        alive_players = [p for p in state.get("players", []) if p.get("is_alive")]
        last_target = state.get("guard_last_target")

        # Find a player who was not guarded last night
        candidates = [p for p in alive_players if p["player_id"] != last_target]

        # Prefer to protect self or known good players
        target = None
        for p in candidates:
            if p["player_id"] != self.player_id:
                target = p["player_id"]
                break

        if not target and candidates:
            target = candidates[0]["player_id"]

        if target:
            self.memory.add_decision("guard", {"target_id": target})
            return {
                "action_type": ActionType.GUARD,
                "target_id": target
            }

        return None

    def get_role_name(self) -> str:
        return "guard"