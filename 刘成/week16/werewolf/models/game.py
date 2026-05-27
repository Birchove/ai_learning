"""Game state models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from werewolf.config import Phase, GameStatus, Camp


class VoteRecord(BaseModel):
    """Record of a vote action."""
    day: int
    voter_id: int
    target_id: int


class SpeechRecord(BaseModel):
    """Record of a speech action."""
    day: int
    phase: str
    player_id: int
    content: str


class NightActionRecord(BaseModel):
    """Record of a night action."""
    night: int
    player_id: int
    action_type: str
    target_id: Optional[int] = None


class GameState(BaseModel):
    """Complete game state."""
    game_id: str
    name: str
    status: str = GameStatus.WAITING
    day: int = 0
    phase: str = Phase.WAITING
    players: list = Field(default_factory=list)
    dead_players: list = Field(default_factory=list)
    vote_records: list[VoteRecord] = Field(default_factory=list)
    speech_records: list[SpeechRecord] = Field(default_factory=list)
    night_actions: list[NightActionRecord] = Field(default_factory=list)
    winner: Optional[str] = None
    # Night tracking
    current_night: int = 0
    # Witch potion status
    witch_can_save: bool = True
    witch_can_poison: bool = True
    # Guard tracking
    guard_last_target: Optional[int] = None
    # Seer tracking
    seer_checks: dict[str, str] = Field(default_factory=dict)  # player_id -> role

    def get_alive_players(self) -> list:
        """Get all alive players."""
        return [p for p in self.players if p.is_alive]

    def get_dead_players(self) -> list:
        """Get all dead players."""
        return [p for p in self.dead_players if p in self.players or not p.is_alive]

    def get_player_by_id(self, player_id: int):
        """Get player by ID."""
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    def get_werewolf_players(self) -> list:
        """Get all werewolf players (alive only for game logic)."""
        return [p for p in self.players if p.role == "werewolf" and p.is_alive]

    def add_speech(self, player_id: int, content: str):
        """Add a speech record."""
        self.speech_records.append(SpeechRecord(
            day=self.day,
            phase=self.phase,
            player_id=player_id,
            content=content
        ))

    def add_vote(self, voter_id: int, target_id: int):
        """Add a vote record."""
        self.vote_records.append(VoteRecord(
            day=self.day,
            voter_id=voter_id,
            target_id=target_id
        ))

    def add_night_action(self, player_id: int, action_type: str, target_id: Optional[int] = None):
        """Add a night action record."""
        self.night_actions.append(NightActionRecord(
            night=self.current_night,
            player_id=player_id,
            action_type=action_type,
            target_id=target_id
        ))