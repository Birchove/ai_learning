"""BM25 索引 — 按 kb_id 分库的内存索引。

v1 简化：每个 kb_id 一份 BM25Okapi 实例。重启后丢失，由 chat_api 启动时从 Milvus 拉取重建。
"""

from typing import Dict, List

import jieba
from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> List[str]:
    """搜索引擎模式 + 全模式叠加，让小语料下 IDF 不那么容易=0。"""
    return [t for t in jieba.lcut_for_search(text) if t.strip()]


class BM25Index:
    def __init__(self) -> None:
        self._raw: Dict[str, List[tuple[str, str]]] = {}
        self._models: Dict[str, BM25Okapi] = {}
        self._chunk_ids: Dict[str, List[str]] = {}
        self._doc_tokens: Dict[str, List[set[str]]] = {}

    def add(self, kb_id: str, chunk_id: str, text: str) -> None:
        self._raw.setdefault(kb_id, []).append((chunk_id, text))

    def build(self, kb_id: str) -> None:
        items = self._raw.get(kb_id, [])
        if not items:
            return
        ids, texts = zip(*items)
        tokenized = [_tokenize(t) for t in texts]
        self._models[kb_id] = BM25Okapi(tokenized)
        self._chunk_ids[kb_id] = list(ids)
        self._doc_tokens[kb_id] = [set(toks) for toks in tokenized]

    def search(self, kb_id: str, query: str, top_k: int) -> List[str]:
        if kb_id not in self._models:
            return []
        q_tokens = _tokenize(query)
        q_set = set(q_tokens)
        scores = self._models[kb_id].get_scores(q_tokens)
        ids = self._chunk_ids[kb_id]
        # 命中过滤：query 与 doc token 有交集才算候选（绕开 IDF=0 全 0 分问题）
        candidates = [
            (cid, score)
            for cid, score, doc_toks in zip(ids, scores, self._doc_tokens[kb_id])
            if q_set & doc_toks
        ]
        ranked = sorted(candidates, key=lambda x: x[1], reverse=True)
        return [cid for cid, _ in ranked[:top_k]]
