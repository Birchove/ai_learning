"""BM25 索引 — 中文分词 + rank_bm25，按 kb_id 分库。"""

import pytest


@pytest.fixture
def index():
    from services.chat_api.retrieval.bm25 import BM25Index
    idx = BM25Index()
    return idx


def test_search_finds_keyword_match(index):
    index.add("kb_001", chunk_id="t1", text="销售额在第三季度大幅下降")
    index.add("kb_001", chunk_id="t2", text="产品质量稳步提升")
    index.build("kb_001")
    hits = index.search("kb_001", "销售额下降", top_k=2)
    assert hits[0] == "t1"


def test_search_isolates_by_kb_id(index):
    index.add("kb_001", chunk_id="a", text="销售额下降")
    index.add("kb_002", chunk_id="b", text="销售额下降")
    index.build("kb_001")
    index.build("kb_002")
    hits1 = index.search("kb_001", "销售额下降", top_k=10)
    hits2 = index.search("kb_002", "销售额下降", top_k=10)
    assert hits1 == ["a"]
    assert hits2 == ["b"]


def test_search_unknown_kb_returns_empty(index):
    assert index.search("kb_does_not_exist", "x", top_k=10) == []


def test_search_top_k_limits_results(index):
    for i in range(5):
        index.add("kb_001", chunk_id=f"c{i}", text=f"第{i}个文档讲销售")
    index.build("kb_001")
    hits = index.search("kb_001", "销售", top_k=3)
    assert len(hits) <= 3


def test_chinese_tokenization_handles_no_spaces(index):
    """没空格的中文也能命中关键词。"""
    index.add("kb_001", chunk_id="x", text="人工智能技术发展迅猛")
    index.build("kb_001")
    hits = index.search("kb_001", "人工智能", top_k=1)
    assert hits == ["x"]
