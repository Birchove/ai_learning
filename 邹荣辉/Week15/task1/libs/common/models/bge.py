"""BGE 文本编码器 wrapper（兼容 small/base/large）。

接口契约：
    encoder = BGEEncoder(model_path, device)
    vecs = encoder.encode(["text1", "text2"])  # → np.ndarray[N, dim]
"""

from typing import List

import numpy as np


class BGEEncoder:
    def __init__(self, model_path: str, device: str = "cuda:0") -> None:
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_path, device=device)

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._model.get_sentence_embedding_dimension()), dtype=np.float32)
        return self._model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True,
        ).astype(np.float32)
