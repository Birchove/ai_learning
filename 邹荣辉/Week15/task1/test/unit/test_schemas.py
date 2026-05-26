"""Pydantic schemas for upload/chat/messages — 跨服务复用。"""

import pytest
from pydantic import ValidationError


def test_upload_response_shape():
    from libs.common.schemas.document import UploadResponse
    r = UploadResponse(doc_id="doc_1", filename="r.pdf", status="pending")
    assert r.model_dump() == {"doc_id": "doc_1", "filename": "r.pdf", "status": "pending"}


def test_document_status_response_shape():
    from libs.common.schemas.document import DocumentStatusResponse
    r = DocumentStatusResponse(doc_id="doc_1", status="parsing", error_msg=None)
    assert r.status == "parsing"


def test_document_status_response_rejects_unknown_status():
    from libs.common.schemas.document import DocumentStatusResponse
    with pytest.raises(ValidationError):
        DocumentStatusResponse(doc_id="d", status="bogus", error_msg=None)


def test_chat_request_requires_kb_id_and_question():
    from libs.common.schemas.chat import ChatRequest
    r = ChatRequest(kb_id="kb_001", question="hi", history=[])
    assert r.kb_id == "kb_001"
    assert r.question == "hi"
    assert r.history == []


def test_chat_request_history_supports_user_assistant_roles():
    from libs.common.schemas.chat import ChatRequest, ChatMessage
    r = ChatRequest(
        kb_id="kb_001",
        question="follow up",
        history=[
            ChatMessage(role="user", content="first"),
            ChatMessage(role="assistant", content="reply"),
        ],
    )
    assert len(r.history) == 2


def test_chat_message_rejects_bogus_role():
    from libs.common.schemas.chat import ChatMessage
    with pytest.raises(ValidationError):
        ChatMessage(role="system_admin", content="x")


def test_citation_carries_filename_page_chapter_image_url():
    from libs.common.schemas.chat import Citation
    c = Citation(
        filename="report.pdf", page=12, chapter="3.2 销售分析",
        image_url="/static/doc_1/figures/fig_3.png",
    )
    assert c.page == 12


def test_parse_task_message_serialises_to_kafka_payload():
    from libs.common.schemas.messages import ParseTaskMessage
    m = ParseTaskMessage(
        task_id="task_1", doc_id="doc_1", kb_id="kb_001",
        local_path="/data/pdfs/doc_1.pdf",
    )
    payload = m.model_dump_json()
    parsed = ParseTaskMessage.model_validate_json(payload)
    assert parsed == m
