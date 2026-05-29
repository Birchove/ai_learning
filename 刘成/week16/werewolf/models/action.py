"""Action models."""

from typing import Optional
from pydantic import BaseModel


class Action(BaseModel):
    """Base action model."""
    player_id: int
    action_type: str
    target_id: Optional[int] = None
    content: Optional[str] = None


class NightAction(BaseModel):
    """Night action with target."""
    player_id: int
    action_type: str
    target_id: Optional[int] = None


class ActionType:
    """Action type constants."""
    VOTE = "vote"
    SPEAK = "speak"
    KILL = "kill"
    SAVE = "save"
    POISON = "poison"
    CHECK = "check"
    GUARD = "guard"
    SHOOT = "shoot"