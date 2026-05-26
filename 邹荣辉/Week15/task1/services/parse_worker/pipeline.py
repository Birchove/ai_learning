"""parse_worker 编排：MinerU 解析 → 切分 → 编码 → 入 Milvus → 更新状态。

设计：
- 所有外部依赖（mineru/bge/clip/indexer）从外部注入，方便测试用 fake。
- 失败必标 failed + error_msg，不抛异常上抛（worker 主循环要继续消费下一条）。
"""

import uuid
from pathlib import Path
from typing import Any, List, Protocol

from libs.common.db.models import ParseStatus
from libs.common.db.repositories import (
    DocumentRepository, ParseTaskRepository,
)
from libs.common.schemas.messages import ParseTaskMessage
from libs.common.storage.paths import StoragePaths
from services.parse_worker.chunker import recursive_chunk
from services.parse_worker.image_chunker import pair_images_with_captions


class _Indexer(Protocol):
    def insert_text(self, rows: List[dict]) -> None: ...
    def insert_image(self, rows: List[dict]) -> None: ...


def _ext_chunk_id(doc_id: str, modality: str, idx: int) -> str:
    return f"{doc_id}:{modality}:{idx}"


def process_one(
    *, msg: ParseTaskMessage, SessionLocal, sp: StoragePaths,
    mineru, bge, clip, indexer: _Indexer,
    chunk_size: int = 500, overlap: int = 50,
) -> None:
    session = SessionLocal()
    repo = ParseTaskRepository(session)
    try:
        repo.mark_status(msg.task_id, ParseStatus.parsing)
        session.commit()

        out_dir = sp.parsed_dir(msg.doc_id)
        parsed = mineru.parse(Path(msg.local_path), out_dir)

        markdown = parsed.markdown_path.read_text(encoding="utf-8")
        text_chunks = recursive_chunk(markdown, chunk_size=chunk_size, overlap=overlap)
        image_chunks = pair_images_with_captions(markdown, base_dir=str(parsed.markdown_path.parent))

        # 文本编码
        text_vecs = bge.encode(text_chunks) if text_chunks else []
        text_rows = [
            {
                "id": _ext_chunk_id(msg.doc_id, "text", i),
                "kb_id": msg.kb_id, "doc_id": msg.doc_id,
                "page": 0, "chunk_idx": i, "modality": "text",
                "content": chunk[:4000],
                "embedding": text_vecs[i].tolist() if len(text_vecs) else [],
            }
            for i, chunk in enumerate(text_chunks)
        ]

        # 图像编码（caption + image 两个信号；v1 只用 image 走 CLIP）
        image_vecs = []
        if image_chunks:
            from PIL import Image
            imgs = [Image.open(c.image_path).convert("RGB") for c in image_chunks]
            image_vecs = clip.encode_image(imgs)
        image_rows = [
            {
                "id": _ext_chunk_id(msg.doc_id, "image", i),
                "kb_id": msg.kb_id, "doc_id": msg.doc_id,
                "page": 0, "chunk_idx": i, "modality": "image",
                "image_path": c.image_path, "caption": c.caption[:1000],
                "embedding": image_vecs[i].tolist() if len(image_vecs) else [],
            }
            for i, c in enumerate(image_chunks)
        ]

        indexer.insert_text(text_rows)
        indexer.insert_image(image_rows)

        # 回填 page_count
        doc = DocumentRepository(session).get(msg.doc_id)
        if doc is not None:
            doc.page_count = parsed.page_count
        repo.mark_status(msg.task_id, ParseStatus.embedded)
        session.commit()
    except Exception as e:
        session.rollback()
        repo.mark_failed(msg.task_id, error_msg=str(e))
        session.commit()
    finally:
        session.close()
