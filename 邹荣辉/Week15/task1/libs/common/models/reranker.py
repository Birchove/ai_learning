"""BGE-Reranker wrapper — 输入 (query, candidates) 返回分数。"""

from typing import List

import numpy as np


class BGEReranker:
    def __init__(self, model_path: str, device: str = "cuda:0") -> None:
        from sentence_transformers import CrossEncoder
        self._model = CrossEncoder(model_path, device=device)

    def rerank(self, query: str, candidates: List[str]) -> np.ndarray:
        if not candidates:
            return np.zeros(0, dtype=np.float32)
        pairs = [[query, c] for c in candidates]
        return np.asarray(self._model.predict(pairs), dtype=np.float32)
