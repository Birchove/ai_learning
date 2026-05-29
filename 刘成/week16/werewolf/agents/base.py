"""Base agent class for all roles."""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from werewolf.llm.qwen_client import QwenClient
from werewolf.memory.role_memory import RoleMemory
from werewolf.llm.prompts import get_role_prompt, THOUGHT_PROMPT, SPEECH_PROMPT, VOTE_PROMPT

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all game agents."""

    def __init__(
        self,
        player_id: int,
        role: str,
        name: str,
        llm_client: Optional[QwenClient] = None
    ):
        self.player_id = player_id
        self.role = role
        self.name = name
        self.llm_client = llm_client or QwenClient()
        self.memory = RoleMemory(player_id, role)
        self._system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt for this agent's role."""
        return get_role_prompt(self.role)

    def think(self, state: dict) -> str:
        """Make a decision based on game state."""
        prompt = THOUGHT_PROMPT.format(state=self._format_state(state))
        response = self.llm_client.chat(self._system_prompt, prompt)
        self.memory.add_observation(f"Thinking: {response}")
        return response

    def speak(self, state: dict) -> str:
        """Generate speech content."""
        prompt = SPEECH_PROMPT.format(
            role=self.role,
            state=self._format_state(state)
        )
        response = self.llm_client.chat(self._system_prompt, prompt)
        self.memory.add_observation(f"Speech: {response}")
        return response

    def vote(self, state: dict) -> int:
        """Make a vote decision. Returns player_id to vote for."""
        history = self.memory.get_recent_conversations(limit=5)
        prompt = VOTE_PROMPT.format(
            role=self.role,
            state=self._format_state(state),
            vote_history=history
        )
        response = self.llm_client.chat(self._system_prompt, prompt)

        # Try to parse player_id from response
        player_id = self._parse_vote_response(response, state)
        if player_id:
            self.memory.add_decision("vote", {"target_id": player_id, "reason": response})
        return player_id or -1

    def night_action(self, state: dict) -> Optional[dict]:
        """Perform night action. Returns action dict or None."""
        return None

    def _format_state(self, state: dict) -> str:
        """Format game state for prompts."""
        lines = [f"Day {state.get('day', 0)}, Phase: {state.get('phase', 'unknown')}"]
        lines.append(f"Your role: {self.role}")
        lines.append(f"Your player_id: {self.player_id}")

        lines.append("\nPlayers:")
        for p in state.get("players", []):
            alive = "alive" if p.get("is_alive") else "dead"
            role = p.get("role", "unknown")
            lines.append(f"  {p['player_id']}: {p['name']} ({alive}, role: {role})")

        if state.get("speech_records"):
            lines.append("\nRecent speeches:")
            for s in state.get("speech_records", [])[-5:]:
                lines.append(f"  Player {s['player_id']}: {s['content'][:100]}")

        if state.get("vote_records"):
            lines.append("\nRecent votes:")
            for v in state.get("vote_records", [])[-5:]:
                lines.append(f"  Player {v['voter_id']} voted for Player {v['target_id']}")

        return "\n".join(lines)

    def _parse_vote_response(self, response: str, state: dict) -> Optional[int]:
        """Parse player_id from vote response."""
        import re
        # Look for patterns like "vote 3" or "player_id: 3" or "3"
        patterns = [
            r'[Vv]ote\s+(?:for\s+)?(?:player\s+)?(\d+)',
            r'player[_ ]?id[:\s]+(\d+)',
            r'(\d+)\s*(?:is|should|will)',
        ]

        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                player_id = int(match.group(1))
                # Validate player exists and is alive
                for p in state.get("players", []):
                    if p["player_id"] == player_id and p.get("is_alive", True):
                        return player_id

        # Default to first alive player if parsing fails
        for p in state.get("players", []):
            if p.get("is_alive", True) and p["player_id"] != self.player_id:
                return p["player_id"]

        return None

    @abstractmethod
    def get_role_name(self) -> str:
        """Get the role name for display."""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.player_id}, role={self.role})"