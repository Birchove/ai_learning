"""upload_api 业务编排：保存 PDF → 写 SQLite → 投 Kafka。"""

import uuid
from pathlib import Path
from typing import Protocol

from libs.common.db.repositories import (
    DocumentRepository, KnowledgeBaseRepository, ParseTaskRepository,
)
from libs.common.schemas.messages import ParseTaskMessage
from libs.common.storage.paths import StoragePaths


class _Producer(Protocol):
    def send(self, msg: ParseTaskMessage) -> None: ...
    def flush(self, timeout: float = ...) -> None: ...


def save_uploaded_pdf(content: bytes, doc_id: str, sp: StoragePaths) -> Path:
    pdf_path = sp.pdf_path(doc_id)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(content)
    return pdf_path


def register_upload(
    session, *, kb_id: str, filename: str, content: bytes,
    sp: StoragePaths, producer: _Producer,
) -> dict:
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    pdf_path = save_uploaded_pdf(content, doc_id, sp)

    KnowledgeBaseRepository(session).get_or_create(kb_id, name=kb_id)
    DocumentRepository(session).create(
        doc_id=doc_id, kb_id=kb_id, filename=filename,
        local_path=str(pdf_path),
        page_count=0,  # 解析阶段再回填
    )
    ParseTaskRepository(session).create_for_doc(task_id, doc_id)
    session.commit()

    producer.send(
        ParseTaskMessage(
            task_id=task_id, doc_id=doc_id, kb_id=kb_id,
            local_path=str(pdf_path),
        )
    )
    return {"doc_id": doc_id, "filename": filename, "status": "pending"}
