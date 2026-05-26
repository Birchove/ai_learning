"""upload_api 的端到端测试 — 通过 FastAPI TestClient。

策略：
- DB 用 :memory: SQLite
- Kafka producer 用 mock（捕获发送的消息）
- 文件存储用 tmp_path

不连任何真实中间件，纯 Python 验证 FastAPI 路由 + 业务编排。
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class _FakeProducer:
    def __init__(self) -> None:
        self.sent = []

    def send(self, msg) -> None:
        self.sent.append(msg)

    def flush(self, timeout: float = 10.0) -> None:
        pass


@pytest.fixture
def app_and_producer(tmp_path):
    from sqlalchemy.pool import StaticPool

    from libs.common.db.models import Base
    from libs.common.storage.paths import StoragePaths
    from services.upload_api.main import build_app

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    producer = _FakeProducer()
    sp = StoragePaths(data_dir=tmp_path)
    sp.ensure_base_dirs()

    app = build_app(SessionLocal=SessionLocal, producer=producer, storage=sp)
    return app, producer, sp


def test_upload_returns_doc_id_and_pending_status(app_and_producer):
    app, producer, sp = app_and_producer
    client = TestClient(app)
    pdf_bytes = b"%PDF-1.4\n%fake\n"
    r = client.post(
        "/upload/document",
        files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"kb_id": "kb_001"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "report.pdf"
    assert body["status"] == "pending"
    assert body["doc_id"]


def test_upload_persists_pdf_to_storage(app_and_producer):
    app, producer, sp = app_and_producer
    client = TestClient(app)
    body = client.post(
        "/upload/document",
        files={"file": ("r.pdf", io.BytesIO(b"%PDF-1.4\n"), "application/pdf")},
        data={"kb_id": "kb_001"},
    ).json()
    assert sp.pdf_path(body["doc_id"]).exists()


def test_upload_publishes_kafka_task(app_and_producer):
    app, producer, sp = app_and_producer
    client = TestClient(app)
    body = client.post(
        "/upload/document",
        files={"file": ("r.pdf", io.BytesIO(b"x"), "application/pdf")},
        data={"kb_id": "kb_001"},
    ).json()
    assert len(producer.sent) == 1
    msg = producer.sent[0]
    assert msg.doc_id == body["doc_id"]
    assert msg.kb_id == "kb_001"


def test_status_endpoint_initially_pending(app_and_producer):
    app, _, _ = app_and_producer
    client = TestClient(app)
    upload = client.post(
        "/upload/document",
        files={"file": ("r.pdf", io.BytesIO(b"x"), "application/pdf")},
        data={"kb_id": "kb_001"},
    ).json()
    r = client.get(f"/documents/{upload['doc_id']}/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    assert body["error_msg"] is None


def test_status_endpoint_unknown_doc_returns_404(app_and_producer):
    app, _, _ = app_and_producer
    client = TestClient(app)
    r = client.get("/documents/does_not_exist/status")
    assert r.status_code == 404


def test_upload_rejects_non_pdf(app_and_producer):
    """v1 只允许 PDF。"""
    app, _, _ = app_and_producer
    client = TestClient(app)
    r = client.post(
        "/upload/document",
        files={"file": ("notes.txt", io.BytesIO(b"x"), "text/plain")},
        data={"kb_id": "kb_001"},
    )
    assert r.status_code == 400
