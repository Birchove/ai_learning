"""parse_worker 主循环 — 由 docker-compose / systemd / 手工启动。

用法：
    python -m services.parse_worker.main
"""

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from libs.common.config import Settings
from libs.common.db.engine import init_schema, make_engine, make_sessionmaker
from libs.common.models.bge import BGEEncoder
from libs.common.models.clip import ChineseCLIPEncoder
from libs.common.models.mineru import MineruParser
from libs.common.mq.consumer import ParseTaskConsumer
from libs.common.storage.paths import StoragePaths
from libs.common.vectorstore import client as vs_client
from libs.common.vectorstore import ops as vs_ops
from services.parse_worker.pipeline import process_one


class _MilvusIndexer:
    def insert_text(self, rows): vs_ops.insert_text_chunks(rows)
    def insert_image(self, rows): vs_ops.insert_image_chunks(rows)


def main() -> None:
    s = Settings()
    logging.basicConfig(level=s.log_level)

    engine = make_engine(s.sqlite_path)
    init_schema(engine)
    SessionLocal = make_sessionmaker(engine)
    sp = StoragePaths(data_dir=Path(s.data_dir), static_url_prefix=s.static_url_prefix)
    sp.ensure_base_dirs()

    vs_client.connect(s.milvus_host, s.milvus_port)
    vs_client.ensure_collections()

    mineru = MineruParser(model_path=s.mineru_model_path)
    bge = BGEEncoder(s.bge_model_path, device=s.torch_device)
    clip = ChineseCLIPEncoder(s.clip_model_path, device=s.torch_device)
    indexer = _MilvusIndexer()

    consumer = ParseTaskConsumer(
        bootstrap_servers=s.kafka_bootstrap_servers,
        group_id=s.kafka_consumer_group,
        topic=s.kafka_parse_topic,
    )
    logging.info("parse_worker started")
    try:
        for msg in consumer.poll_messages():
            logging.info("processing %s", msg.task_id)
            process_one(
                msg=msg, SessionLocal=SessionLocal, sp=sp,
                mineru=mineru, bge=bge, clip=clip, indexer=indexer,
                chunk_size=s.chunk_size, overlap=s.chunk_overlap,
            )
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
