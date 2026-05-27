"""Pydantic schemas for API requests and responses."""

from typing import Optional
from pydantic import BaseModel


class CreateGameRequest(BaseModel):
    """Request to create a new game."""
    name: str
    player_count: dict[str, int]  # {"werewolf": 2, "seer": 1, "villager": 4}
    ai_count: int = 0  # Number of AI players
    human_count: int = 0  # Number of human players


class CreateGameResponse(BaseModel):
    """Response after creating a game."""
    game_id: str
    name: str
    status: str
    message: str = "Game created successfully"


class PlayerInfo(BaseModel):
    """Player information."""
    player_id: int
    name: str
    role: str
    is_alive: bool
    is_ai: bool


class GameStateResponse(BaseModel):
    """Full game state response."""
    game_id: str
    name: str
    status: str
    day: int
    phase: str
    winner: Optional[str] = None
    players: list[PlayerInfo]
    message: str = ""


class GameViewResponse(BaseModel):
    """Response for a player's view of the game."""
    game_id: str
    day: int
    phase: str
    my_id: int
    my_role: str
    my_is_alive: bool
    players: list[dict]
    seer_checks: dict[str, str] = {}
    speech_records: list[dict]
    vote_records: list[dict]
    night_actions: list[dict]


class SubmitActionRequest(BaseModel):
    """Request to submit a player action."""
    player_id: int
    action_type: str  # vote, speak, special
    target_id: Optional[int] = None
    content: Optional[str] = None


class SubmitActionResponse(BaseModel):
    """Response after submitting an action."""
    success: bool
    message: str


class AddPlayerRequest(BaseModel):
    """Request to add a player to a game."""
    name: str
    is_ai: bool = True


class AddPlayerResponse(BaseModel):
    """Response after adding a player."""
    player_id: int
    name: str
    role: str
    is_ai: bool
    success: bool
    message: str


class StartGameResponse(BaseModel):
    """Response after starting a game."""
    success: bool
    game_id: str
    message: str


class SpeechRecordResponse(BaseModel):
    """Speech record for log output."""
    day: int
    phase: str
    player_id: int
    content: str


class VoteRecordResponse(BaseModel):
    """Vote record for log output."""
    day: int
    voter_id: int
    target_id: int


class GameLogResponse(BaseModel):
    """Full game log response."""
    game_id: str
    status: str
    winner: Optional[str]
    day: int
    players: list[dict]
    dead_players: list[dict]
    speech_records: list[SpeechRecordResponse]
    vote_records: list[VoteRecordResponse]
    message: str = ""


class GameListResponse(BaseModel):
    """List of all games."""
    games: list[dict]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None