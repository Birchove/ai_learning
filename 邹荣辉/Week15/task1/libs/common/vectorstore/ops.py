"""Milvus 读写操作。"""

from typing import Any, Dict, List, Sequence

import numpy as np
from pymilvus import Collection

from libs.common.vectorstore.client import get_image_collection, get_text_collection


def insert_text_chunks(rows: List[Dict[str, Any]]) -> None:
    """rows: [{id, kb_id, doc_id, page, chunk_idx, modality, content, embedding}]"""
    if not rows:
        return
    col = get_text_collection()
    col.insert(_to_columns(rows, ["id", "kb_id", "doc_id", "page", "chunk_idx",
                                  "modality", "content", "embedding"]))
    col.flush()


def insert_image_chunks(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    col = get_image_collection()
    col.insert(_to_columns(rows, ["id", "kb_id", "doc_id", "page", "chunk_idx",
                                  "modality", "image_path", "caption", "embedding"]))
    col.flush()


def search_text(kb_id: str, query_embedding: Sequence[float], top_k: int) -> List[Dict[str, Any]]:
    return _search(get_text_collection(), kb_id, query_embedding, top_k,
                   output_fields=["doc_id", "page", "chunk_idx", "content"])


def search_image(kb_id: str, query_embedding: Sequence[float], top_k: int) -> List[Dict[str, Any]]:
    return _search(get_image_collection(), kb_id, query_embedding, top_k,
                   output_fields=["doc_id", "page", "chunk_idx", "image_path", "caption"])


def _to_columns(rows: List[Dict[str, Any]], fields: List[str]) -> List[List[Any]]:
    return [[r[f] for r in rows] for f in fields]


def _search(col: Collection, kb_id: str, qv: Sequence[float], top_k: int,
            output_fields: List[str]) -> List[Dict[str, Any]]:
    results = col.search(
        data=[list(qv)],
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"nprobe": 16}},
        limit=top_k,
        expr=f'kb_id == "{kb_id}"',
        output_fields=output_fields,
    )
    out: List[Dict[str, Any]] = []
    for hit in results[0]:
        item = {"id": hit.id, "score": hit.distance}
        for f in output_fields:
            item[f] = hit.entity.get(f)
        out.append(item)
    return out
