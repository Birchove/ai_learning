"""Hunter agent."""

from typing import Optional
from werewolf.agents.base import BaseAgent


class HunterAgent(BaseAgent):
    """Agent for hunter role."""

    def get_role_name(self) -> str:
        return "hunter"

    def should_shoot(self, state: dict) -> Optional[int]:
        """Determine if and who to shoot when dying."""
        # Look for confirmed werewolf
        seer_checks = state.get("seer_checks", {})
        alive_players = [p for p in state.get("players", []) if p.get("is_alive")]

        # Find werewolf by seer info
        for pid_str, role in seer_checks.items():
            if role == "werewolf":
                pid = int(pid_str)
                for p in alive_players:
                    if p["player_id"] == pid:
                        return pid

        # Fallback to suspicious player
        return None