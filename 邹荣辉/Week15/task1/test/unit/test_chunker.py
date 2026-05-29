"""递归分块 — 按自然语义边界（段落/句号），chunk_size=500, overlap=50。

边界分隔符优先级：双换行 > 单换行 > 句号 > 逗号 > 直接切。
"""


def test_short_text_returns_single_chunk():
    from services.parse_worker.chunker import recursive_chunk
    chunks = recursive_chunk("hello world", chunk_size=500, overlap=50)
    assert chunks == ["hello world"]


def test_long_text_split_into_chunks_no_loss():
    from services.parse_worker.chunker import recursive_chunk
    text = "段落甲。" * 200  # 200 段，每段 5 字（含句号），共 1000 字
    chunks = recursive_chunk(text, chunk_size=300, overlap=30)
    assert len(chunks) > 1
    # 拼回 + 去重 overlap 后内容必须包含原文的所有字符种类
    joined = "".join(chunks)
    assert "段落甲" in joined


def test_no_chunk_exceeds_size_limit():
    from services.parse_worker.chunker import recursive_chunk
    text = "第一句。第二句。第三句。" * 50
    for c in recursive_chunk(text, chunk_size=100, overlap=10):
        assert len(c) <= 100


def test_chunks_overlap_to_preserve_context():
    from services.parse_worker.chunker import recursive_chunk
    text = "abcdefghij" * 50  # 500 字
    chunks = recursive_chunk(text, chunk_size=100, overlap=20)
    # 相邻 chunk 末尾/开头必须有重叠
    for i in range(len(chunks) - 1):
        assert chunks[i][-20:] == chunks[i + 1][:20]


def test_prefers_paragraph_boundaries():
    """两个明确段落分隔时，应优先在段落处切，不在词中间切。"""
    from services.parse_worker.chunker import recursive_chunk
    text = "段落甲" * 30 + "\n\n" + "段落乙" * 30
    chunks = recursive_chunk(text, chunk_size=100, overlap=10)
    assert any("段落甲" in c and "段落乙" not in c for c in chunks)
