from typing import List, Literal, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    kb_id: str
    question: str
    history: List[ChatMessage] = []


class Citation(BaseModel):
    filename: str
    page: int
    chapter: Optional[str] = None
    image_url: Optional[str] = None
