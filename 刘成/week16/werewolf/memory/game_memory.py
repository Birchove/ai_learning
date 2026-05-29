"""Global game memory for all agents."""

from typing import Optional


class GameMemory:
    """Global memory shared across all game events."""

    def __init__(self):
        self.game_events: list[dict] = []
        self.phase_changes: list[dict] = []
        self.player_deaths: list[dict] = []
        self.vote_records: list[dict] = []
        self.speeches: list[dict] = []

    def add_event(self, event_type: str, data: dict):
        """Add a game event."""
        self.game_events.append({
            "type": event_type,
            "data": data
        })

    def add_phase_change(self, old_phase: str, new_phase: str, day: int):
        """Record a phase change."""
        self.phase_changes.append({
            "old_phase": old_phase,
            "new_phase": new_phase,
            "day": day
        })

    def add_death(self, player_id: int, role: str, cause: str):
        """Record a player death."""
        self.player_deaths.append({
            "player_id": player_id,
            "role": role,
            "cause": cause
        })

    def add_speech(self, player_id: int, content: str, day: int):
        """Add a speech record."""
        self.speeches.append({
            "player_id": player_id,
            "content": content,
            "day": day
        })

    def get_player_speeches(self, player_id: int) -> list[dict]:
        """Get all speeches by a specific player."""
        return [s for s in self.speeches if s["player_id"] == player_id]

    def get_dead_players(self) -> list[dict]:
        """Get all dead players."""
        return self.player_deaths

    def get_day_events(self, day: int) -> list[dict]:
        """Get all events for a specific day."""
        return [e for e in self.game_events if e.get("day") == day]

    def get_summary(self) -> dict:
        """Get a summary of game memory."""
        return {
            "total_events": len(self.game_events),
            "phase_changes": len(self.phase_changes),
            "deaths": len(self.player_deaths),
            "speeches": len(self.speeches),
        }