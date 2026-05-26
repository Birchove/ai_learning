"""Chinese-CLIP 图文编码器 wrapper（兼容 base/large）。

接口契约：
    enc = ChineseCLIPEncoder(model_path, device)
    text_vec = enc.encode_text(["query"])     # → np.ndarray[N, dim]
    img_vec = enc.encode_image([PIL.Image])    # → np.ndarray[N, dim]
"""

from typing import List

import numpy as np
from PIL import Image


class ChineseCLIPEncoder:
    def __init__(self, model_path: str, device: str = "cuda:0") -> None:
        import torch
        from transformers import ChineseCLIPModel, ChineseCLIPProcessor
        self.device = device
        self.processor = ChineseCLIPProcessor.from_pretrained(model_path)
        self.model = ChineseCLIPModel.from_pretrained(model_path).to(device).eval()
        self._torch = torch
        self.dim = self.model.config.projection_dim

    def encode_text(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        with self._torch.no_grad():
            inputs = self.processor(text=texts, padding=True, return_tensors="pt").to(self.device)
            feats = self.model.get_text_features(**inputs)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.cpu().numpy().astype(np.float32)

    def encode_image(self, images: List[Image.Image]) -> np.ndarray:
        if not images:
            return np.zeros((0, self.dim), dtype=np.float32)
        with self._torch.no_grad():
            inputs = self.processor(images=images, return_tensors="pt").to(self.device)
            feats = self.model.get_image_features(**inputs)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        return feats.cpu().numpy().astype(np.float32)
