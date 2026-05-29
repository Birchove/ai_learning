"""Kafka producer 薄封装 — 投 ParseTaskMessage。"""

import json
from typing import Optional

from confluent_kafka import Producer

from libs.common.schemas.messages import ParseTaskMessage


class ParseTaskProducer:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self.topic = topic
        self._p = Producer({"bootstrap.servers": bootstrap_servers})

    def send(self, msg: ParseTaskMessage) -> None:
        self._p.produce(self.topic, msg.model_dump_json().encode("utf-8"))
        self._p.poll(0)

    def flush(self, timeout: float = 10.0) -> None:
        self._p.flush(timeout)
