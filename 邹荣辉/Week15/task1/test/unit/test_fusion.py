"""RRF 融合 — 三路召回结果按 Reciprocal Rank Fusion 合并。"""


def test_rrf_promotes_items_in_multiple_lists():
    from services.chat_api.retrieval.fusion import rrf_fuse
    a = ["x", "y", "z"]
    b = ["y", "w"]
    c = ["y"]
    fused = rrf_fuse([a, b, c], k=60)
    # y 在三个列表都靠前 → 排第一
    assert fused[0] == "y"


def test_rrf_handles_single_list():
    from services.chat_api.retrieval.fusion import rrf_fuse
    fused = rrf_fuse([["a", "b", "c"]], k=60)
    assert fused == ["a", "b", "c"]


def test_rrf_returns_unique_ids():
    from services.chat_api.retrieval.fusion import rrf_fuse
    fused = rrf_fuse([["a", "b"], ["a", "c"]], k=60)
    assert sorted(fused) == ["a", "b", "c"]


def test_rrf_score_formula():
    """显式验证 1/(k+rank) 公式。"""
    from services.chat_api.retrieval.fusion import rrf_scores
    scores = rrf_scores([["a", "b"]], k=10)
    # rank 1-based: a → 1/(10+1), b → 1/(10+2)
    assert scores["a"] == 1 / 11
    assert scores["b"] == 1 / 12
