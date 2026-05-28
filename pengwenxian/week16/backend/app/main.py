from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .game_data import GameService

service = GameService()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI 狼人杀 Agent Team API",
        description="提供样例对局、时间线和复盘数据的基础后端服务。",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "provider": "qwen",
            "model_ready": "true" if service.llm_client.is_ready() else "false",
            "model": service.llm_client.model,
        }

    @app.get("/api/games")
    def list_games():
        return service.list_games()

    @app.post("/api/games/ai")
    def create_ai_game():
        return service.create_ai_game()

    @app.post("/api/games/{game_id}/stop")
    def stop_game(game_id: str):
        game = service.stop_game(game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="未找到对应对局")
        return game

    @app.get("/api/games/{game_id}")
    def get_game(game_id: str):
        game = service.get_game(game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="未找到对应对局")
        return game

    @app.get("/api/games/{game_id}/replay")
    def get_replay(game_id: str):
        replay = service.get_replay(game_id)
        if replay is None:
            game = service.get_game(game_id)
            if game is None:
                raise HTTPException(status_code=404, detail="未找到对应复盘")
            raise HTTPException(status_code=409, detail="对局尚未结束，复盘仍在生成中")
        return replay

    return app


app = create_app()
