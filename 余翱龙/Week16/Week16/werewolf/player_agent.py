"""玩家Agent基类"""
import os
from abc import ABC, abstractmethod
from game_state import GameState, Player, Role
from message_queue import MessageBus, Message, MessageType


class PlayerAgent(ABC):
    def __init__(self, player_id: int, name: str, role: Role):
        self.player_id = player_id
        self.name = name
        self.role = role
        self.game_state: GameState = None
        self.message_bus: MessageBus = None

    def set_context(self, game_state: GameState, message_bus: MessageBus):
        self.game_state = game_state
        self.message_bus = message_bus

    def receive_messages(self) -> list[Message]:
        return self.message_bus.get_messages_for(self.player_id)

    @abstractmethod
    def on_night_turn(self) -> int | None:
        """夜间行动，返回目标玩家ID（如果有）"""
        pass

    @abstractmethod
    def on_day_phase(self, is_first_day: bool) -> str:
        """白天发言"""
        pass

    @abstractmethod
    def on_vote_phase(self) -> int:
        """投票阶段，返回投票目标ID"""
        pass

    def call_llm(self, prompt: str) -> str:
        """调用LLM获取回复"""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=os.environ.get("DASHSCOPE_API_KEY"),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            response = client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "system", "content": f"You are a player in a Werewolf game. Your role is {self.role.value}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM调用失败: {e}"

    def get_alive_players_info(self) -> str:
        alive = self.game_state.get_alive_players()
        info = []
        for p in alive:
            if p.id != self.player_id:
                info.append(f"Player {p.id}: {p.name}")
        return ", ".join(info) if info else "无"