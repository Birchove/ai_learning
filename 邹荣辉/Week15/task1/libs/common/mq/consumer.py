"""Kafka consumer 薄封装 — 拉 ParseTaskMessage。"""

from typing import Iterator

from confluent_kafka import Consumer, KafkaError

from libs.common.schemas.messages import ParseTaskMessage


class ParseTaskConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str, topic: str) -> None:
        self._c = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )
        self._c.subscribe([topic])

    def poll_messages(self, timeout: float = 1.0) -> Iterator[ParseTaskMessage]:
        while True:
            msg = self._c.poll(timeout)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise RuntimeError(f"Kafka error: {msg.error()}")
            payload = msg.value().decode("utf-8")
            yield ParseTaskMessage.model_validate_json(payload)
            self._c.commit(msg, asynchronous=False)

    def close(self) -> None:
        self._c.close()
