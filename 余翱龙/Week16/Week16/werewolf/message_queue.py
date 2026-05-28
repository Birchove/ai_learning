"""消息传递机制"""
from dataclasses import dataclass
from typing import Any
from enum import Enum


class MessageType(Enum):
    GLOBAL = "global"
    PRIVATE = "private"
    PHASE_CHANGE = "phase_change"
    DEATH = "death"
    SKILL_RESULT = "skill_result"
    VOTE = "vote"


@dataclass
class Message:
    msg_type: MessageType
    content: Any
    recipient_id: int = 0
    sender_id: int = 0


class MessageBus:
    def __init__(self):
        self.messages: list[Message] = []

    def publish(self, message: Message):
        self.messages.append(message)

    def get_messages_for(self, player_id: int) -> list[Message]:
        return [m for m in self.messages
                if m.msg_type == MessageType.GLOBAL
                or m.recipient_id == player_id
                or m.sender_id == player_id]

    def clear(self):
        self.messages.clear()

    def get_global_messages(self) -> list[Message]:
        return [m for m in self.messages if m.msg_type == MessageType.GLOBAL]