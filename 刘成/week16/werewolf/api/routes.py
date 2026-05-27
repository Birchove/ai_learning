"""REST API routes for werewolf game."""

from typing import Optional
from fastapi import APIRouter, HTTPException, WebSocket
from werewolf.engine.game_engine import GameEngine
from werewolf.agents.factory import create_agent
from werewolf.llm.qwen_client import QwenClient, get_client
from werewolf.config import AI_NAME_PREFIX

# Global game manager (in-memory for now)
games: dict[str, GameEngine] = {}
agents: dict[str, dict[int, any]] = {}

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post("")
async def create_game(request: dict):
    """Create a new game."""
    try:
        name = request.get("name", "Default Game")
        player_count = request.get("player_count", {
            "werewolf": 3,
            "seer": 1,
            "witch": 1,
            "guard": 1,
            "hunter": 1,
            "villager": 3,
        })
        ai_count = request.get("ai_count", 0)
        human_count = request.get("human_count", 0)

        engine = GameEngine()
        game_id, state = engine.create_game(name, player_count)
        engine.set_player_count(player_count)
        engine.setup_players(ai_count, human_count)

        games[game_id] = engine
        agents[game_id] = {}

        return {
            "game_id": game_id,
            "name": name,
            "status": state.status,
            "message": "Game created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_games():
    """List all games."""
    return {
        "games": [
            {
                "game_id": g.state.game_id,
                "name": g.state.name,
                "status": g.state.status,
                "day": g.state.day,
                "phase": g.state.phase,
            }
            for g in games.values()
        ]
    }


@router.get("/{game_id}")
async def get_game(game_id: str):
    """Get game details."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    state = engine.state

    return {
        "game_id": game_id,
        "name": state.name,
        "status": state.status,
        "day": state.day,
        "phase": state.phase,
        "winner": state.winner,
        "players": [
            {
                "player_id": p.player_id,
                "name": p.name,
                "role": p.role if not p.is_alive else "unknown",
                "is_alive": p.is_alive,
                "is_ai": p.is_ai,
            }
            for p in state.players
        ],
        "message": ""
    }


@router.delete("/{game_id}")
async def delete_game(game_id: str):
    """Delete a game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    del games[game_id]
    if game_id in agents:
        del agents[game_id]

    return {"success": True, "message": "Game deleted"}


@router.post("/{game_id}/players")
async def add_player(game_id: str, request: dict):
    """Add a player to a game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    if engine.state.status != "waiting":
        raise HTTPException(status_code=400, detail="Cannot add players to ongoing game")

    name = request.get("name", f"Player_{len(engine.state.players) + 1}")
    is_ai = request.get("is_ai", True)

    from werewolf.models.player import Player
    player_id = len(engine.state.players) + 1
    player = Player(
        player_id=player_id,
        name=name,
        role="unknown",  # Role assigned on game start
        is_alive=True,
        is_ai=is_ai,
    )
    engine.state.players.append(player)

    return {
        "player_id": player_id,
        "name": name,
        "role": "unknown",
        "is_ai": is_ai,
        "success": True,
        "message": "Player added"
    }


@router.post("/{game_id}/start")
async def start_game(game_id: str):
    """Start a game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    if engine.state.status != "waiting":
        raise HTTPException(status_code=400, detail="Game already started")

    try:
        engine.start_game()
        return {
            "success": True,
            "game_id": game_id,
            "message": "Game started"
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/action")
async def submit_action(game_id: str, request: dict):
    """Submit a player action."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    player_id = request.get("player_id")
    action_type = request.get("action_type")
    target_id = request.get("target_id")
    content = request.get("content")

    player = engine.state.get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    try:
        if action_type == "speak" and content:
            engine.add_speech(player_id, content)
        elif action_type == "vote" and target_id:
            engine.add_vote(player_id, target_id)
        elif action_type == "kill":
            engine.process_night_action(player_id, "kill", target_id)
        elif action_type == "check":
            engine.process_night_action(player_id, "check", target_id)
        elif action_type == "save":
            engine.process_night_action(player_id, "save", target_id)
        elif action_type == "poison":
            engine.process_night_action(player_id, "poison", target_id)
        elif action_type == "guard":
            engine.process_night_action(player_id, "guard", target_id)

        return {"success": True, "message": "Action processed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{game_id}/state")
async def get_game_state(game_id: str, player_id: int = 1):
    """Get game state visible to a specific player."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    visible = engine.get_visible_state(player_id)

    return visible


@router.get("/{game_id}/log")
async def get_game_log(game_id: str):
    """Get full game log."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    summary = engine.get_game_summary()

    return summary


@router.get("/{game_id}/speeches")
async def get_speeches(game_id: str):
    """Get all speeches from the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    return {
        "speeches": [
            {"day": s.day, "player_id": s.player_id, "content": s.content}
            for s in engine.state.speech_records
        ]
    }


@router.post("/{game_id}/next_phase")
async def advance_phase(game_id: str):
    """Advance to next phase (for AI or manual control)."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    try:
        day, phase = engine.next_phase()

        # Execute night actions if transitioning from night
        if phase == "day":
            results = engine.execute_night_actions()
            # Process kills
            if results.get("kill_target"):
                kill_target = results["kill_target"]
                saved = results.get("saved")
                if kill_target != saved:
                    engine.eliminate_player(kill_target, "werewolf_kill")

        # Check win condition
        winner = engine.check_win_condition()

        return {
            "success": True,
            "day": day,
            "phase": phase,
            "winner": winner
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/auto_run")
async def auto_run_game(game_id: str, rounds: int = 20):
    """Run the game automatically with AI players."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    from werewolf.engine.auto_runner import create_auto_runner

    engine = games[game_id]

    # Start game if not started
    if engine.state.status == "waiting":
        engine.start_game()

    runner = create_auto_runner(engine)

    # Run the game
    result = await runner.run_game(max_rounds=rounds)

    return {
        "success": True,
        "game_id": game_id,
        "result": result
    }


@router.get("/{game_id}/save")
async def save_game_log(game_id: str):
    """Save game log to JSON file."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    engine = games[game_id]
    filepath = engine.save_to_json()

    return {
        "success": True,
        "game_id": game_id,
        "filepath": filepath
    }