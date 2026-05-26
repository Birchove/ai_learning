"""配置 — 验证 README 锁定的默认值不会被静默改动。"""


def test_default_chunk_params_match_readme(monkeypatch):
    monkeypatch.delenv("CHUNK_SIZE", raising=False)
    monkeypatch.delenv("CHUNK_OVERLAP", raising=False)
    from libs.common.config import Settings
    s = Settings()
    assert s.chunk_size == 500
    assert s.chunk_overlap == 50


def test_default_top_k_match_readme(monkeypatch):
    for k in ["BM25_TOP_K", "BGE_TOP_K", "CLIP_TOP_K", "RERANK_TOP_K"]:
        monkeypatch.delenv(k, raising=False)
    from libs.common.config import Settings
    s = Settings()
    assert s.bm25_top_k == 100
    assert s.bge_top_k == 100
    assert s.clip_top_k == 50
    assert s.rerank_top_k == 10


def test_generation_budget_match_readme(monkeypatch):
    for k in ["QWEN_VL_MAX_INPUT_TOKENS", "QWEN_VL_MAX_OUTPUT_TOKENS", "QWEN_VL_MAX_IMAGES"]:
        monkeypatch.delenv(k, raising=False)
    from libs.common.config import Settings
    s = Settings()
    assert s.qwen_vl_max_input_tokens == 4000
    assert s.qwen_vl_max_output_tokens == 1000
    assert s.qwen_vl_max_images == 3


def test_env_overrides_defaults(monkeypatch):
    monkeypatch.setenv("CHUNK_SIZE", "256")
    from libs.common.config import Settings
    s = Settings()
    assert s.chunk_size == 256
