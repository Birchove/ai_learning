"""Villager agent."""

from werewolf.agents.base import BaseAgent


class VillagerAgent(BaseAgent):
    """Agent for villager role."""

    def get_role_name(self) -> str:
        return "villager"

    def think(self, state: dict) -> str:
        """Villager reasoning about who might be werewolf."""
        return super().think(state)