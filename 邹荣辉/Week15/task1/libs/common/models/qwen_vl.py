"""Qwen-VL 多模态生成 wrapper — 兼容 Qwen2-VL 与 Qwen2.5-VL，流式输出。

接口契约：
    gen = QwenVLGenerator(model_path, device)
    for token in gen.stream_generate(messages, max_new_tokens):
        yield token
"""

from typing import Any, Dict, Iterator, List


def _load_model(model_path: str, torch_dtype, device: str):
    """根据权重目录里的 config 自动选 Qwen2VL / Qwen2_5_VL 类。"""
    import json
    from pathlib import Path
    cfg_path = Path(model_path) / "config.json"
    arch = ""
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        archs = cfg.get("architectures") or []
        arch = archs[0] if archs else ""
    if "Qwen2_5_VL" in arch:
        from transformers import Qwen2_5_VLForConditionalGeneration as _Cls
    else:
        from transformers import Qwen2VLForConditionalGeneration as _Cls
    return _Cls.from_pretrained(model_path, torch_dtype=torch_dtype).to(device).eval()


class QwenVLGenerator:
    def __init__(self, model_path: str, device: str = "cuda:0",
                 dtype: str = "bfloat16") -> None:
        import torch
        from transformers import AutoProcessor
        self.device = device
        self.processor = AutoProcessor.from_pretrained(model_path)
        torch_dtype = getattr(torch, dtype)
        self.model = _load_model(model_path, torch_dtype, device)
        self._torch = torch

    def stream_generate(self, messages: List[Dict[str, Any]],
                        max_new_tokens: int = 1000) -> Iterator[str]:
        from threading import Thread

        from qwen_vl_utils import process_vision_info
        from transformers import TextIteratorStreamer

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text], images=image_inputs, videos=video_inputs,
            padding=True, return_tensors="pt",
        ).to(self.device)

        streamer = TextIteratorStreamer(
            self.processor.tokenizer, skip_prompt=True, skip_special_tokens=True,
        )
        gen_kwargs = dict(**inputs, max_new_tokens=max_new_tokens, streamer=streamer)
        thread = Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()
        for token in streamer:
            yield token
        thread.join()
