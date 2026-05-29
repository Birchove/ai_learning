"""WebSocket handler for real-time game streaming."""

import json
import logging
from typing import Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class GameWebSocket:
    """Manages WebSocket connections for a game."""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"WebSocket connected for game {self.game_id}, total connections: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.connections:
            self.connections.remove(websocket)
            logger.info(f"WebSocket disconnected for game {self.game_id}, remaining: {len(self.connections)}")

    async def broadcast(self, event_type: str, data: dict):
        """Broadcast an event to all connected clients."""
        message = json.dumps({
            "event_type": event_type,
            "data": data
        })

        for connection in self.connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")


# Global WebSocket manager
ws_manager: dict[str, GameWebSocket] = {}


def get_ws_manager(game_id: str) -> GameWebSocket:
    """Get or create WebSocket manager for a game."""
    if game_id not in ws_manager:
        ws_manager[game_id] = GameWebSocket(game_id)
    return ws_manager[game_id]


async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for game streaming."""
    manager = get_ws_manager(game_id)
    await manager.connect(websocket)

    try:
        while True:
            # Wait for messages (keep connection alive)
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)