"""FastAPI main entry point."""

import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from werewolf.api.routes import router as games_router
from werewolf.api.ws_handler import websocket_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI app
app = FastAPI(
    title="Werewolf Multi-Agent Game API",
    description="API for狼人杀 multi-agent game system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(games_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Werewolf Multi-Agent Game API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/api/games/{game_id}/stream")
async def game_stream(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for game streaming."""
    await websocket_endpoint(websocket, game_id)


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()