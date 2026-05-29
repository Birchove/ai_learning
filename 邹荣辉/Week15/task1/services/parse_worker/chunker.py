"""递归分块 — 按自然语义边界（段落 → 单换行 → 句号 → 逗号 → 空格 → 硬切）。"""

from typing import List

_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "，", " "]


def _split_at_level(text: str, max_size: int, level: int) -> List[str]:
    if len(text) <= max_size:
        return [text]
    if level >= len(_SEPARATORS):
        # 最底层：硬切
        return [text[i : i + max_size] for i in range(0, len(text), max_size)]
    sep = _SEPARATORS[level]
    if sep not in text:
        return _split_at_level(text, max_size, level + 1)

    # 用 sep 切，把所有片段（保留 sep 后缀）尽量合并到 <= max_size 的桶中
    raw = text.split(sep)
    pieces = [p + sep for p in raw[:-1]] + ([raw[-1]] if raw[-1] else [])

    out: List[str] = []
    buf = ""
    for piece in pieces:
        if len(piece) > max_size:
            if buf:
                out.append(buf)
                buf = ""
            out.extend(_split_at_level(piece, max_size, level + 1))
        elif len(buf) + len(piece) <= max_size:
            buf += piece
        else:
            if buf:
                out.append(buf)
            buf = piece
    if buf:
        out.append(buf)
    return out


def _apply_overlap(parts: List[str], overlap: int) -> List[str]:
    if overlap <= 0 or len(parts) <= 1:
        return parts
    out: List[str] = [parts[0]]
    for i in range(1, len(parts)):
        prev_tail = out[-1][-overlap:]
        out.append(prev_tail + parts[i])
    return out


def recursive_chunk(text: str, chunk_size: int, overlap: int) -> List[str]:
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    body_size = max(1, chunk_size - overlap)
    parts = _split_at_level(text, body_size, level=0)
    return _apply_overlap(parts, overlap)
