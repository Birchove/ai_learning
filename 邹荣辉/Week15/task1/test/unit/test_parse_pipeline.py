"""parse_worker pipeline 测试 — 用 fake parser/encoder/indexer 注入。"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@dataclass
class _FakeParsed:
    markdown_path: Path
    figures_dir: Path
    page_count: int


class _FakeMineru:
    def parse(self, pdf_path, output_dir):
        from PIL import Image
        figs = Path(output_dir) / "figures"
        figs.mkdir(parents=True, exist_ok=True)
        md_path = Path(output_dir) / "content.md"
        md_path.write_text(
            "第一段说明销售情况。\n\n"
            "![](figures/fig_1.png)\n\n"
            "图1：销售柱状图\n\n"
            "第二段是产品分析。",
            encoding="utf-8",
        )
        # 真正的 1x1 PNG，让 PIL 能打开
        Image.new("RGB", (1, 1), color="red").save(figs / "fig_1.png")
        return _FakeParsed(markdown_path=md_path, figures_dir=figs, page_count=3)


class _FakeBGE:
    def encode(self, texts: List[str]) -> np.ndarray:
        return np.zeros((len(texts), 1024), dtype=np.float32)


class _FakeCLIP:
    def encode_image(self, images) -> np.ndarray:
        return np.zeros((len(images), 768), dtype=np.float32)


class _FakeIndexer:
    def __init__(self) -> None:
        self.text_rows = []
        self.image_rows = []

    def insert_text(self, rows): self.text_rows.extend(rows)
    def insert_image(self, rows): self.image_rows.extend(rows)


@pytest.fixture
def deps(tmp_path):
    from libs.common.db.models import Base
    from libs.common.storage.paths import StoragePaths

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    sp = StoragePaths(data_dir=tmp_path)
    sp.ensure_base_dirs()

    return SessionLocal, sp, _FakeMineru(), _FakeBGE(), _FakeCLIP(), _FakeIndexer()


def _seed(SessionLocal, sp, kb_id="kb_001", doc_id="doc_a"):
    from libs.common.db.repositories import (
        DocumentRepository, KnowledgeBaseRepository, ParseTaskRepository,
    )
    s = SessionLocal()
    KnowledgeBaseRepository(s).get_or_create(kb_id, name="d")
    pdf = sp.pdf_path(doc_id)
    pdf.write_bytes(b"%PDF-1.4\n")
    DocumentRepository(s).create(doc_id, kb_id, "r.pdf", str(pdf), 0)
    ParseTaskRepository(s).create_for_doc("task_1", doc_id)
    s.commit()
    s.close()


def test_pipeline_marks_status_embedded_on_success(deps):
    from libs.common.db.models import ParseStatus
    from libs.common.db.repositories import ParseTaskRepository
    from libs.common.schemas.messages import ParseTaskMessage
    from services.parse_worker.pipeline import process_one

    SessionLocal, sp, mineru, bge, clip, indexer = deps
    _seed(SessionLocal, sp)

    process_one(
        msg=ParseTaskMessage(
            task_id="task_1", doc_id="doc_a", kb_id="kb_001",
            local_path=str(sp.pdf_path("doc_a")),
        ),
        SessionLocal=SessionLocal, sp=sp,
        mineru=mineru, bge=bge, clip=clip, indexer=indexer,
        chunk_size=500, overlap=50,
    )
    s = SessionLocal()
    status, err = ParseTaskRepository(s).latest_status_for_doc("doc_a")
    s.close()
    assert status == ParseStatus.embedded
    assert err is None


def test_pipeline_writes_text_and_image_rows(deps):
    from libs.common.schemas.messages import ParseTaskMessage
    from services.parse_worker.pipeline import process_one

    SessionLocal, sp, mineru, bge, clip, indexer = deps
    _seed(SessionLocal, sp)

    process_one(
        msg=ParseTaskMessage(
            task_id="task_1", doc_id="doc_a", kb_id="kb_001",
            local_path=str(sp.pdf_path("doc_a")),
        ),
        SessionLocal=SessionLocal, sp=sp,
        mineru=mineru, bge=bge, clip=clip, indexer=indexer,
        chunk_size=500, overlap=50,
    )
    assert len(indexer.text_rows) > 0
    assert len(indexer.image_rows) == 1  # fake markdown 里只有一张图
    # 元数据完整
    for r in indexer.text_rows + indexer.image_rows:
        assert r["kb_id"] == "kb_001"
        assert r["doc_id"] == "doc_a"
        assert "id" in r and "embedding" in r


def test_pipeline_marks_failed_on_parser_error(deps):
    from libs.common.db.models import ParseStatus
    from libs.common.db.repositories import ParseTaskRepository
    from libs.common.schemas.messages import ParseTaskMessage
    from services.parse_worker.pipeline import process_one

    SessionLocal, sp, _, bge, clip, indexer = deps
    _seed(SessionLocal, sp)

    class _BoomMineru:
        def parse(self, *a, **kw): raise RuntimeError("MinerU OOM")

    process_one(
        msg=ParseTaskMessage(
            task_id="task_1", doc_id="doc_a", kb_id="kb_001",
            local_path=str(sp.pdf_path("doc_a")),
        ),
        SessionLocal=SessionLocal, sp=sp,
        mineru=_BoomMineru(), bge=bge, clip=clip, indexer=indexer,
        chunk_size=500, overlap=50,
    )
    s = SessionLocal()
    status, err = ParseTaskRepository(s).latest_status_for_doc("doc_a")
    s.close()
    assert status == ParseStatus.failed
    assert "OOM" in err
