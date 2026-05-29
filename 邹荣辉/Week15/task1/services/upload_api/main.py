"""upload_api FastAPI 应用 — build_app(deps) 让测试可以注入假 producer / DB。"""

from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from libs.common.db.repositories import DocumentRepository, ParseTaskRepository
from libs.common.schemas.document import DocumentStatusResponse, UploadResponse
from libs.common.storage.paths import StoragePaths
from services.upload_api.service import register_upload


def build_app(*, SessionLocal, producer, storage: StoragePaths) -> FastAPI:
    app = FastAPI(title="upload-api")

    def get_session():
        s = SessionLocal()
        try:
            yield s
        finally:
            s.close()

    @app.post("/upload/document", response_model=UploadResponse)
    async def upload_document(
        kb_id: str = Form(...),
        file: UploadFile = File(...),
        session=Depends(get_session),
    ):
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="only PDF files are accepted")
        content = await file.read()
        result = register_upload(
            session, kb_id=kb_id, filename=file.filename, content=content,
            sp=storage, producer=producer,
        )
        return UploadResponse(**result)

    @app.get("/documents/{doc_id}/status", response_model=DocumentStatusResponse)
    def get_status(doc_id: str, session=Depends(get_session)):
        if DocumentRepository(session).get(doc_id) is None:
            raise HTTPException(status_code=404, detail="document not found")
        latest = ParseTaskRepository(session).latest_status_for_doc(doc_id)
        if latest is None:
            raise HTTPException(status_code=404, detail="no parse task")
        status, err = latest
        return DocumentStatusResponse(doc_id=doc_id, status=status.value, error_msg=err)

    return app
