"""Agent factory for creating role agents."""

from werewolf.agents.base import BaseAgent
from werewolf.agents.villager import VillagerAgent
from werewolf.agents.werewolf import WerewolfAgent
from werewolf.agents.seer import SeerAgent
from werewolf.agents.witch import WitchAgent
from werewolf.agents.guard import GuardAgent
from werewolf.agents.hunter import HunterAgent
from werewolf.llm.qwen_client import QwenClient


def create_agent(role: str, player_id: int, name: str, llm_client: QwenClient = None) -> BaseAgent:
    """Factory function to create an agent based on role.

    Args:
        role: Role name (villager, werewolf, seer, witch, guard, hunter)
        player_id: Player ID
        name: Player name
        llm_client: Optional LLM client

    Returns:
        BaseAgent instance for the specified role
    """
    agents = {
        "villager": VillagerAgent,
        "werewolf": WerewolfAgent,
        "seer": SeerAgent,
        "witch": WitchAgent,
        "guard": GuardAgent,
        "hunter": HunterAgent,
    }

    agent_class = agents.get(role.lower(), VillagerAgent)
    return agent_class(player_id, role, name, llm_client)


def create_agents_for_game(players: list[dict], llm_client: QwenClient = None) -> dict[int, BaseAgent]:
    """Create agents for all players in a game.

    Args:
        players: List of player dicts with player_id, name, role
        llm_client: Optional LLM client

    Returns:
        Dict mapping player_id to BaseAgent
    """
    agents = {}
    for p in players:
        agent = create_agent(
            role=p["role"],
            player_id=p["player_id"],
            name=p["name"],
            llm_client=llm_client
        )
        agents[p["player_id"]] = agent
    return agents