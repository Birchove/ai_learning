"""Tests for agents."""

import pytest
from unittest.mock import MagicMock, patch
from werewolf.agents.base import BaseAgent
from werewolf.agents.villager import VillagerAgent
from werewolf.agents.werewolf import WerewolfAgent
from werewolf.agents.seer import SeerAgent
from werewolf.agents.witch import WitchAgent
from werewolf.agents.guard import GuardAgent
from werewolf.agents.hunter import HunterAgent
from werewolf.agents.factory import create_agent
from werewolf.config import Role, ActionType


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self):
        self.calls = []

    def chat(self, system_prompt, user_prompt, max_tokens=2000):
        self.calls.append({"system": system_prompt, "user": user_prompt})
        return "Mock response"

    def chat_with_history(self, system_prompt, history, max_tokens=2000):
        self.calls.append({"system": system_prompt, "history": history})
        return "Mock response with history"


class TestBaseAgent:
    """Test cases for BaseAgent class."""

    def test_agent_creation(self):
        """Test agent creation."""
        agent = VillagerAgent(player_id=1, role="villager", name="Test Player")

        assert agent.player_id == 1
        assert agent.role == "villager"
        assert agent.name == "Test Player"
        assert agent.memory is not None

    def test_speak(self):
        """Test speech generation."""
        mock_client = MockLLMClient()
        agent = VillagerAgent(player_id=1, role="villager", name="Test Player", llm_client=mock_client)

        state = {
            "day": 1,
            "phase": "day",
            "players": [
                {"player_id": 1, "name": "P1", "is_alive": True},
                {"player_id": 2, "name": "P2", "is_alive": True},
            ]
        }

        speech = agent.speak(state)
        assert speech == "Mock response"
        assert len(mock_client.calls) == 1


class TestWerewolfAgent:
    """Test cases for WerewolfAgent."""

    def test_night_action_kill(self):
        """Test werewolf kill action."""
        mock_client = MockLLMClient()
        agent = WerewolfAgent(player_id=1, role="werewolf", name="Werewolf 1", llm_client=mock_client)

        state = {
            "day": 1,
            "phase": "night",
            "players": [
                {"player_id": 1, "name": "W1", "is_alive": True, "role": "werewolf"},
                {"player_id": 2, "name": "V1", "is_alive": True, "role": "villager"},
                {"player_id": 3, "name": "V2", "is_alive": True, "role": "villager"},
            ]
        }

        action = agent.night_action(state)
        assert action is not None
        assert action["action_type"] == ActionType.KILL
        assert action["target_id"] in [2, 3]


class TestSeerAgent:
    """Test cases for SeerAgent."""

    def test_night_action_check(self):
        """Test seer check action."""
        mock_client = MockLLMClient()
        agent = SeerAgent(player_id=1, role="seer", name="Seer 1", llm_client=mock_client)

        state = {
            "day": 1,
            "phase": "night",
            "players": [
                {"player_id": 1, "name": "S1", "is_alive": True, "role": "seer"},
                {"player_id": 2, "name": "V1", "is_alive": True, "role": "unknown"},
                {"player_id": 3, "name": "V2", "is_alive": True, "role": "unknown"},
            ],
            "seer_checks": {}
        }

        action = agent.night_action(state)
        assert action is not None
        assert action["action_type"] == ActionType.CHECK
        assert action["target_id"] == 2


class TestAgentFactory:
    """Test cases for agent factory."""

    def test_create_villager(self):
        """Test creating villager agent."""
        agent = create_agent("villager", 1, "Test")
        assert isinstance(agent, VillagerAgent)
        assert agent.role == "villager"

    def test_create_werewolf(self):
        """Test creating werewolf agent."""
        agent = create_agent("werewolf", 1, "Test")
        assert isinstance(agent, WerewolfAgent)
        assert agent.role == "werewolf"

    def test_create_seer(self):
        """Test creating seer agent."""
        agent = create_agent("seer", 1, "Test")
        assert isinstance(agent, SeerAgent)
        assert agent.role == "seer"

    def test_create_witch(self):
        """Test creating witch agent."""
        agent = create_agent("witch", 1, "Test")
        assert isinstance(agent, WitchAgent)
        assert agent.role == "witch"

    def test_create_guard(self):
        """Test creating guard agent."""
        agent = create_agent("guard", 1, "Test")
        assert isinstance(agent, GuardAgent)
        assert agent.role == "guard"

    def test_create_hunter(self):
        """Test creating hunter agent."""
        agent = create_agent("hunter", 1, "Test")
        assert isinstance(agent, HunterAgent)
        assert agent.role == "hunter"

    def test_create_unknown_role_defaults_to_villager(self):
        """Test unknown role defaults to villager."""
        agent = create_agent("unknown_role", 1, "Test")
        assert isinstance(agent, VillagerAgent)