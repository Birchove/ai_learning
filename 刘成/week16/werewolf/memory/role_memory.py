"""Role-specific memory for each agent."""

from typing import Optional


class RoleMemory:
    """Memory stored by each role agent."""

    def __init__(self, player_id: int, role: str):
        self.player_id = player_id
        self.role = role
        self.conversations: list[dict] = []
        self.observations: list[str] = []
        self.decisions: list[dict] = []
        self.suspicious_players: list[int] = []
        self.trusted_players: list[int] = []

    def add_observation(self, observation: str):
        """Add an observation from the game."""
        self.observations.append(observation)

    def add_conversation(self, speaker_id: int, content: str):
        """Add a conversation record."""
        self.conversations.append({
            "speaker_id": speaker_id,
            "content": content
        })

    def add_decision(self, decision_type: str, decision: dict):
        """Add a decision record."""
        self.decisions.append({
            "type": decision_type,
            "decision": decision
        })

    def mark_suspicious(self, player_id: int):
        """Mark a player as suspicious."""
        if player_id not in self.suspicious_players:
            self.suspicious_players.append(player_id)

    def mark_trusted(self, player_id: int):
        """Mark a player as trusted."""
        if player_id not in self.trusted_players:
            self.trusted_players.append(player_id)

    def get_recent_observations(self, limit: int = 10) -> list[str]:
        """Get recent observations."""
        return self.observations[-limit:]

    def get_recent_conversations(self, limit: int = 10) -> list[dict]:
        """Get recent conversations."""
        return self.conversations[-limit:]

    def get_context_summary(self) -> str:
        """Get a summary of memory context."""
        return f"Role: {self.role}, Observations: {len(self.observations)}, Decisions: {len(self.decisions)}"