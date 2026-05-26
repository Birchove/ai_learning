"""SQLite 模型单元测试 —— 用 :memory: 库，不连真实 SQLite 文件。"""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session


@pytest.fixture
def session():
    from libs.common.db.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_knowledge_base_can_be_inserted_and_read_back(session):
    from libs.common.db.models import KnowledgeBase

    kb = KnowledgeBase(id="kb_001", name="default")
    session.add(kb)
    session.commit()

    fetched = session.get(KnowledgeBase, "kb_001")
    assert fetched is not None
    assert fetched.name == "default"
    assert fetched.created_at is not None


def test_document_links_to_knowledge_base_and_stores_metadata(session):
    from libs.common.db.models import Document, KnowledgeBase

    session.add(KnowledgeBase(id="kb_001", name="default"))
    session.add(
        Document(
            id="doc_abc",
            kb_id="kb_001",
            filename="report.pdf",
            local_path="/data/pdfs/doc_abc.pdf",
            page_count=42,
        )
    )
    session.commit()

    doc = session.get(Document, "doc_abc")
    assert doc.kb_id == "kb_001"
    assert doc.filename == "report.pdf"
    assert doc.local_path == "/data/pdfs/doc_abc.pdf"
    assert doc.page_count == 42
    assert doc.created_at is not None


def test_document_with_unknown_kb_id_is_rejected(session):
    """外键必须强制存在 —— 文档不能挂在一个不存在的知识库下。"""
    from sqlalchemy.exc import IntegrityError
    from libs.common.db.models import Document

    session.execute(__import__("sqlalchemy").text("PRAGMA foreign_keys=ON"))
    session.add(
        Document(
            id="doc_orphan",
            kb_id="kb_does_not_exist",
            filename="x.pdf",
            local_path="/tmp/x.pdf",
            page_count=1,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_parse_task_status_enum_has_four_values():
    """README 锁定的四个状态：pending / parsing / embedded / failed。"""
    from libs.common.db.models import ParseStatus

    assert {s.value for s in ParseStatus} == {"pending", "parsing", "embedded", "failed"}


def _seed_document(session, doc_id="doc_a", kb_id="kb_001"):
    from libs.common.db.models import Document, KnowledgeBase

    session.add(KnowledgeBase(id=kb_id, name="default"))
    session.add(
        Document(
            id=doc_id,
            kb_id=kb_id,
            filename=f"{doc_id}.pdf",
            local_path=f"/data/pdfs/{doc_id}.pdf",
            page_count=1,
        )
    )
    session.commit()


def test_parse_task_defaults_to_pending(session):
    from libs.common.db.models import ParseStatus, ParseTask

    _seed_document(session)
    task = ParseTask(id="task_1", doc_id="doc_a")
    session.add(task)
    session.commit()

    fetched = session.get(ParseTask, "task_1")
    assert fetched.status == ParseStatus.pending
    assert fetched.error_msg is None
    assert fetched.created_at is not None
    assert fetched.updated_at is not None


def test_parse_task_can_record_failure(session):
    from libs.common.db.models import ParseStatus, ParseTask

    _seed_document(session)
    task = ParseTask(
        id="task_2",
        doc_id="doc_a",
        status=ParseStatus.failed,
        error_msg="MinerU OOM",
    )
    session.add(task)
    session.commit()

    fetched = session.get(ParseTask, "task_2")
    assert fetched.status == ParseStatus.failed
    assert fetched.error_msg == "MinerU OOM"
