"""SQLite 数据访问层 — 业务层只调这里，不直接写 ORM。"""

from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.common.db.models import (
    Document, KnowledgeBase, ParseStatus, ParseTask,
)


class KnowledgeBaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(self, kb_id: str, name: str) -> KnowledgeBase:
        kb = self.session.get(KnowledgeBase, kb_id)
        if kb is None:
            kb = KnowledgeBase(id=kb_id, name=name)
            self.session.add(kb)
            self.session.flush()
        return kb


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self, doc_id: str, kb_id: str, filename: str,
        local_path: str, page_count: int,
    ) -> Document:
        doc = Document(
            id=doc_id, kb_id=kb_id, filename=filename,
            local_path=local_path, page_count=page_count,
        )
        self.session.add(doc)
        self.session.flush()
        return doc

    def get(self, doc_id: str) -> Optional[Document]:
        return self.session.get(Document, doc_id)


class ParseTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_for_doc(self, task_id: str, doc_id: str) -> ParseTask:
        task = ParseTask(id=task_id, doc_id=doc_id, status=ParseStatus.pending)
        self.session.add(task)
        self.session.flush()
        return task

    def get(self, task_id: str) -> Optional[ParseTask]:
        return self.session.get(ParseTask, task_id)

    def mark_status(self, task_id: str, status: ParseStatus) -> None:
        task = self.get(task_id)
        task.status = status

    def mark_failed(self, task_id: str, error_msg: str) -> None:
        task = self.get(task_id)
        task.status = ParseStatus.failed
        task.error_msg = error_msg

    def latest_status_for_doc(
        self, doc_id: str,
    ) -> Optional[Tuple[ParseStatus, Optional[str]]]:
        stmt = (
            select(ParseTask)
            .where(ParseTask.doc_id == doc_id)
            .order_by(ParseTask.updated_at.desc())
            .limit(1)
        )
        task = self.session.execute(stmt).scalar_one_or_none()
        if task is None:
            return None
        return task.status, task.error_msg
