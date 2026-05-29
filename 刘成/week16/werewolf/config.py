"""Configuration for werewolf game."""

import os
from typing import Optional

# Qwen API Configuration
DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY", "sk-8916beb8ce594373890f25d8afc8f81e")
DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# Game Configuration
DEFAULT_MODEL: str = "qwen-plus"

# Classic game player count configuration
CLASSIC_CONFIG: dict[str, int] = {
    "werewolf": 3,
    "seer": 1,
    "witch": 1,
    "guard": 1,
    "hunter": 1,
    "villager": 3,
}

# Minimum players for a valid game
MIN_PLAYERS: int = 6

# Maximum players
MAX_PLAYERS: int = 12

# Game phases
class Phase:
    WAITING = "waiting"
    NIGHT = "night"
    DAY = "day"
    VOTE = "vote"
    DEAD_SPEECH = "dead_speech"

# Game status
class GameStatus:
    WAITING = "waiting"
    RUNNING = "running"
    ENDED = "ended"

# Roles
class Role:
    VILLAGER = "villager"
    WEREWOLF = "werewolf"
    SEER = "seer"
    WITCH = "witch"
    GUARD = "guard"
    HUNTER = "hunter"

# Camps (for win condition)
class Camp:
    GOOD = "good"
    WEREWOLF = "werewolf"
    NEUTRAL = "neutral"

# Action types
class ActionType:
    VOTE = "vote"
    SPEAK = "speak"
    KILL = "kill"
    SAVE = "save"
    POISON = "poison"
    CHECK = "check"
    GUARD = "guard"
    SHOOT = "shoot"

# Player name prefixes for AI
AI_NAME_PREFIX: str = "AI_Player"