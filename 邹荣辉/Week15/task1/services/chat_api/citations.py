"""引用：构造 + 去重。"""

from pathlib import Path
from typing import List, Optional

from libs.common.schemas.chat import Citation
from libs.common.storage.paths import StoragePaths


def build_citation(
    modality: str, filename: str, page: int, chapter: Optional[str],
    image_path: Optional[str], sp: StoragePaths,
) -> Citation:
    image_url: Optional[str] = None
    if modality == "image" and image_path:
        image_url = sp.to_static_url(Path(image_path))
    return Citation(filename=filename, page=page, chapter=chapter, image_url=image_url)


def dedup_citations(items: List[Citation]) -> List[Citation]:
    seen: dict[tuple[str, int], Citation] = {}
    for c in items:
        key = (c.filename, c.page)
        if key not in seen:
            seen[key] = c
            continue
        # 已有同键引用：合并 image_url（优先非空）和 chapter
        prev = seen[key]
        merged = Citation(
            filename=c.filename,
            page=c.page,
            chapter=prev.chapter or c.chapter,
            image_url=prev.image_url or c.image_url,
        )
        seen[key] = merged
    return list(seen.values())
