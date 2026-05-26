from typing import Literal, Optional
from pydantic import BaseModel, Field

ParseStatusLiteral = Literal["pending", "parsing", "embedded", "failed"]


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: ParseStatusLiteral


class DocumentStatusResponse(BaseModel):
    doc_id: str
    status: ParseStatusLiteral
    error_msg: Optional[str] = None
