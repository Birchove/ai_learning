"""图 + caption 配对 — 解析 markdown 中 ![alt](path)，捕获相邻段落作 caption。"""

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import List

_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_CAPTION_HINT = re.compile(r"^(图|表|Figure|Table|Fig\.)\s*\d", re.IGNORECASE)


@dataclass
class ImageChunk:
    image_path: str
    caption: str


def _resolve(base_dir: str, rel: str) -> str:
    if rel.startswith("/") or rel.startswith("http"):
        return rel
    return str(PurePosixPath(base_dir) / rel)


def pair_images_with_captions(markdown: str, base_dir: str) -> List[ImageChunk]:
    paragraphs = [p.strip() for p in markdown.split("\n\n")]
    out: List[ImageChunk] = []
    for i, para in enumerate(paragraphs):
        m = _IMG_RE.search(para)
        if not m:
            continue
        img_path = _resolve(base_dir, m.group(1).strip())
        caption = ""
        # 优先看下一段（更常见的 markdown 习惯）
        if i + 1 < len(paragraphs) and _CAPTION_HINT.match(paragraphs[i + 1]):
            caption = paragraphs[i + 1]
        elif i > 0 and _CAPTION_HINT.match(paragraphs[i - 1]):
            caption = paragraphs[i - 1]
        out.append(ImageChunk(image_path=img_path, caption=caption))
    return out
