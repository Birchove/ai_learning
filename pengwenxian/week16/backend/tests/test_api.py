from fastapi.testclient import TestClient

from backend.app.game_data import GameService
from backend.app.main import create_app
import backend.app.main as main_module


class FakeQwenClient:
    model = "qwen3.6-35b-a3b"

    def is_ready(self) -> bool:
        return True

    def chat_json(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.6, max_tokens: int = 600):
        if "key_turning_points" in user_prompt:
            return {
                "summary": "测试复盘摘要",
                "key_turning_points": ["转折点1", "转折点2", "转折点3"],
                "winning_reason": "测试胜因",
                "losing_reason": "测试败因",
                "collaboration_note": "测试协作观察",
            }
        if '"speech"' in user_prompt:
            return {"speech": "测试发言", "thought": "测试思考"}
        if "use_antidote" in user_prompt:
            return {"use_antidote": False, "poison_target_seat": None, "reason": "测试用药", "thought": "测试保守用药"}
        return {"target_seat": 1, "reason": "测试选择", "thought": "测试固定选择"}

main_module.service = GameService(llm_client=FakeQwenClient(), background=False, step_delay=0)
client = TestClient(create_app())


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["provider"] == "qwen"


def test_games_endpoints():
    create_response = client.post("/api/games/ai")
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["id"].startswith("game_ai_")

    list_response = client.get("/api/games")
    assert list_response.status_code == 200
    games = list_response.json()
    assert len(games) >= 1

    detail_response = client.get(f"/api/games/{created['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert len(detail["players"]) == 9
    assert len(detail["timeline"]) >= 3
    assert len(detail["decision_traces"]) > 0

    replay_response = client.get(f"/api/games/{created['id']}/replay")
    assert replay_response.status_code == 200
    assert "summary" in replay_response.json()


def test_stop_game_endpoint():
    create_response = client.post("/api/games/ai")
    created = create_response.json()

    stop_response = client.post(f"/api/games/{created['id']}/stop")

    assert stop_response.status_code == 200
    assert stop_response.json()["id"] == created["id"]
