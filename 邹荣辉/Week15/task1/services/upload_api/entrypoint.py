"""upload_api 启动入口。

用法：
    uvicorn services.upload_api.entrypoint:app --port 8001
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from libs.common.config import Settings
from libs.common.db.engine import init_schema, make_engine, make_sessionmaker
from libs.common.mq.producer import ParseTaskProducer
from libs.common.storage.paths import StoragePaths
from services.upload_api.main import build_app


def _bootstrap():
    s = Settings()
    engine = make_engine(s.sqlite_path)
    init_schema(engine)
    SessionLocal = make_sessionmaker(engine)
    sp = StoragePaths(data_dir=Path(s.data_dir), static_url_prefix=s.static_url_prefix)
    sp.ensure_base_dirs()
    producer = ParseTaskProducer(s.kafka_bootstrap_servers, s.kafka_parse_topic)
    return build_app(SessionLocal=SessionLocal, producer=producer, storage=sp)


app = _bootstrap()
