"""Kafka 消息体 — 三个服务对齐字段名的唯一出处。"""

from pydantic import BaseModel


class ParseTaskMessage(BaseModel):
    task_id: str
    doc_id: str
    kb_id: str
    local_path: str
