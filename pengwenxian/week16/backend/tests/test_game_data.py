import re
import time

from backend.app.game_data import GameService


class FakeQwenClient:
    model = "qwen3.6-35b-a3b"

    def is_ready(self) -> bool:
        return True

    def chat_json(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.6, max_tokens: int = 600):
        if "key_turning_points" in user_prompt:
            return {
                "summary": "测试环境下生成的 AI 总结。",
                "key_turning_points": ["首轮票型形成优势。", "关键身份信息被建立。", "终局票型收束。"],
                "winning_reason": "获胜阵营在投票与信息利用上更稳。",
                "losing_reason": "失败阵营在公开发言中暴露了协作问题。",
                "collaboration_note": "整体协作节奏符合预期。",
            }

        if '"speech"' in user_prompt:
            return {"speech": "我建议今天重点观察票型和发言逻辑。", "thought": "先观察发言与票型。"}

        if "use_antidote" in user_prompt:
            return {"use_antidote": False, "poison_target_seat": None, "reason": "测试环境保守用药。", "thought": "先不交技能。"}

        seats = [int(item) for item in re.findall(r"\d+", user_prompt)]
        target = seats[0] if seats else 1
        return {"target_seat": target, "reason": "测试环境固定选择首个候选。", "thought": "按固定策略选择。"}


class SlowFakeQwenClient(FakeQwenClient):
    def chat_json(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.6, max_tokens: int = 600):
        time.sleep(0.05)
        return super().chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def test_game_service_generates_detail_and_replay():
    service = GameService(llm_client=FakeQwenClient(), background=False, step_delay=0)

    created = service.create_ai_game()
    detail = service.get_game(created.id)
    replay = service.get_replay(created.id)

    assert detail is not None
    assert replay is not None
    assert detail.id == created.id
    assert len(detail.players) == 9
    assert sum(player.role == "狼人" for player in detail.players) == 3
    assert sum(player.role == "平民" for player in detail.players) == 3
    assert detail.status == "completed"
    assert detail.replay_ready is True
    assert len(detail.decision_traces) > 0
    assert replay.game_id == detail.id
    assert len(replay.key_turning_points) == 3


def test_game_service_can_create_and_fetch_ai_game():
    service = GameService(llm_client=FakeQwenClient(), background=False, step_delay=0)

    created = service.create_ai_game()
    detail = service.get_game(created.id)
    replay = service.get_replay(created.id)

    assert detail is not None
    assert replay is not None
    assert detail.title == created.title
    assert replay.metrics["model"] == "qwen3.6-35b-a3b"


def test_game_service_can_stop_running_game():
    service = GameService(llm_client=SlowFakeQwenClient(), background=True, step_delay=0.1)

    created = service.create_ai_game()
    service.stop_game(created.id)
    time.sleep(0.3)
    detail = service.get_game(created.id)

    assert detail is not None
    assert detail.status == "stopped"
    assert detail.replay_ready is False
