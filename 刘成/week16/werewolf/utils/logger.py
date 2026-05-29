"""Logging utilities."""

import json
import logging
from datetime import datetime
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def log_game_event(game_id: str, event_type: str, data: dict[str, Any]):
    """Log a structured game event."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "game_id": game_id,
        "event_type": event_type,
        "data": data
    }
    logging.info(f"GAME_EVENT: {json.dumps(log_entry)}")


def log_agent_action(game_id: str, player_id: int, role: str, action_type: str, details: dict[str, Any]):
    """Log an agent action."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "game_id": game_id,
        "player_id": player_id,
        "role": role,
        "action_type": action_type,
        "details": details
    }
    logging.info(f"AGENT_ACTION: {json.dumps(log_entry)}")


def log_phase_change(game_id: str, day: int, old_phase: str, new_phase: str):
    """Log a phase change."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "game_id": game_id,
        "day": day,
        "old_phase": old_phase,
        "new_phase": new_phase
    }
    logging.info(f"PHASE_CHANGE: {json.dumps(log_entry)}")


def log_game_result(game_id: str, winner: str, reason: str):
    """Log game result."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "game_id": game_id,
        "winner": winner,
        "reason": reason
    }
    logging.info(f"GAME_RESULT: {json.dumps(log_entry)}")