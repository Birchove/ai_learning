"""Repositories — knowledge_base / document / parse_task 三类操作的唯一入口。"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


@pytest.fixture
def session():
    from libs.common.db.models import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_knowledge_base_repo_get_or_create_is_idempotent(session):
    from libs.common.db.repositories import KnowledgeBaseRepository
    repo = KnowledgeBaseRepository(session)
    kb1 = repo.get_or_create("kb_001", name="default")
    kb2 = repo.get_or_create("kb_001", name="default")
    session.commit()
    assert kb1.id == kb2.id
    assert session.query(type(kb1)).count() == 1


def test_document_repo_create_returns_persisted_doc(session):
    from libs.common.db.repositories import DocumentRepository, KnowledgeBaseRepository
    KnowledgeBaseRepository(session).get_or_create("kb_001", name="default")
    doc = DocumentRepository(session).create(
        doc_id="doc_a", kb_id="kb_001", filename="r.pdf",
        local_path="/data/pdfs/doc_a.pdf", page_count=10,
    )
    session.commit()
    assert doc.id == "doc_a"
    assert doc.created_at is not None


def test_parse_task_repo_creates_pending_task(session):
    from libs.common.db.repositories import (
        DocumentRepository, KnowledgeBaseRepository, ParseTaskRepository,
    )
    from libs.common.db.models import ParseStatus
    KnowledgeBaseRepository(session).get_or_create("kb_001", name="default")
    DocumentRepository(session).create(
        doc_id="doc_a", kb_id="kb_001", filename="r.pdf",
        local_path="/x.pdf", page_count=1,
    )
    repo = ParseTaskRepository(session)
    task = repo.create_for_doc("task_1", "doc_a")
    session.commit()
    assert task.status == ParseStatus.pending


def test_parse_task_repo_mark_status_persists(session):
    from libs.common.db.repositories import (
        DocumentRepository, KnowledgeBaseRepository, ParseTaskRepository,
    )
    from libs.common.db.models import ParseStatus
    KnowledgeBaseRepository(session).get_or_create("kb_001", name="d")
    DocumentRepository(session).create("doc_a", "kb_001", "r.pdf", "/x", 1)
    repo = ParseTaskRepository(session)
    repo.create_for_doc("task_1", "doc_a")
    session.commit()

    repo.mark_status("task_1", ParseStatus.parsing)
    session.commit()
    assert repo.get("task_1").status == ParseStatus.parsing


def test_parse_task_repo_mark_failed_records_error(session):
    from libs.common.db.repositories import (
        DocumentRepository, KnowledgeBaseRepository, ParseTaskRepository,
    )
    from libs.common.db.models import ParseStatus
    KnowledgeBaseRepository(session).get_or_create("kb_001", name="d")
    DocumentRepository(session).create("doc_a", "kb_001", "r.pdf", "/x", 1)
    repo = ParseTaskRepository(session)
    repo.create_for_doc("task_1", "doc_a")
    session.commit()

    repo.mark_failed("task_1", error_msg="MinerU OOM")
    session.commit()
    t = repo.get("task_1")
    assert t.status == ParseStatus.failed
    assert t.error_msg == "MinerU OOM"


def test_parse_task_repo_status_for_doc(session):
    """支持 GET /documents/{doc_id}/status 查询：拿最新一条 task 的 status。"""
    from libs.common.db.repositories import (
        DocumentRepository, KnowledgeBaseRepository, ParseTaskRepository,
    )
    from libs.common.db.models import ParseStatus
    KnowledgeBaseRepository(session).get_or_create("kb_001", name="d")
    DocumentRepository(session).create("doc_a", "kb_001", "r.pdf", "/x", 1)
    repo = ParseTaskRepository(session)
    repo.create_for_doc("task_1", "doc_a")
    repo.mark_status("task_1", ParseStatus.embedded)
    session.commit()
    assert repo.latest_status_for_doc("doc_a") == (ParseStatus.embedded, None)
