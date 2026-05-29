"""chat_api 端到端测试 — 全部依赖用 fake 注入。

测试目标：
- 三路召回 → RRF → rerank → 取 top-10 给 LLM
- SSE 流式按 token 返回
- 引用结构正确（含 image_url 重写）
- 多轮历史会被传给 LLM
"""

import json
import pytest
from fastapi.testclient import TestClient


class _FakeBGE:
    def encode(self, texts):
        import numpy as np
        return np.zeros((len(texts), 1024), dtype=np.float32)


class _FakeCLIP:
    def encode_text(self, texts):
        import numpy as np
        return np.zeros((len(texts), 768), dtype=np.float32)


class _FakeReranker:
    def rerank(self, query, candidates):
        # 倒序：让我们能看出 reranker 真生效
        import numpy as np
        return np.array([float(i) for i in range(len(candidates), 0, -1)], dtype=np.float32)


class _FakeQwen:
    def __init__(self):
        self.last_messages = None

    def stream_generate(self, messages, max_new_tokens=1000):
        self.last_messages = messages
        for tok in ["销售", "额", "下降"]:
            yield tok


class _FakeRetriever:
    """注入预制的检索结果 — 三路召回 + Milvus 文本/图像查询。"""
    def __init__(self):
        self.text_hits = []  # List[dict]
        self.image_hits = []
        self.bm25_ids = []

    def text_search(self, kb_id, qv, top_k):
        return self.text_hits[:top_k]

    def image_search(self, kb_id, qv, top_k):
        return self.image_hits[:top_k]

    def bm25_search(self, kb_id, query, top_k):
        return self.bm25_ids[:top_k]


@pytest.fixture
def app_and_fakes(tmp_path):
    # 重置 sse_starlette 的全局 AppStatus.should_exit_event；
    # 它是模块级 asyncio.Event，pytest 多次创建 TestClient 会跨 loop。
    from sse_starlette.sse import AppStatus
    AppStatus.should_exit_event = None  # type: ignore[assignment]

    from libs.common.storage.paths import StoragePaths
    from services.chat_api.main import build_app

    sp = StoragePaths(data_dir=tmp_path, static_url_prefix="/static")
    sp.ensure_base_dirs()

    bge = _FakeBGE()
    clip = _FakeCLIP()
    reranker = _FakeReranker()
    qwen = _FakeQwen()
    retriever = _FakeRetriever()

    # 注入真实的 image 文件，让 to_static_url 不报错
    fig_dir = sp.parsed_dir("doc_a") / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    (fig_dir / "fig_1.png").write_bytes(b"\x89PNG")
    img_path = str(fig_dir / "fig_1.png")

    retriever.text_hits = [
        {"id": "doc_a:text:0", "score": 0.9, "doc_id": "doc_a", "page": 12,
         "chunk_idx": 0, "content": "销售额下降明显"},
        {"id": "doc_a:text:1", "score": 0.5, "doc_id": "doc_a", "page": 13,
         "chunk_idx": 1, "content": "Q3 表现疲软"},
    ]
    retriever.image_hits = [
        {"id": "doc_a:image:0", "score": 0.7, "doc_id": "doc_a", "page": 12,
         "chunk_idx": 0, "image_path": img_path, "caption": "图1：销售柱状图"},
    ]
    retriever.bm25_ids = ["doc_a:text:0", "doc_a:text:1"]

    # doc_id → filename 简单映射
    filename_lookup = {"doc_a": "report.pdf"}

    app = build_app(
        bge=bge, clip=clip, reranker=reranker, qwen=qwen,
        retriever=retriever, sp=sp, filename_lookup=filename_lookup,
        bm25_top_k=100, bge_top_k=100, clip_top_k=50, rerank_top_k=10,
        max_images=3,
    )
    return app, qwen, retriever


def _read_sse_events(response) -> list[dict]:
    events = []
    for line in response.iter_lines():
        if not line:
            continue
        # httpx 的 iter_lines 已经按行分割，且 line 是 str
        if line.startswith("data: "):
            payload = line[len("data: "):]
            events.append(json.loads(payload))
    return events


def test_chat_streams_tokens_and_emits_done(app_and_fakes):
    app, _, _ = app_and_fakes
    client = TestClient(app)
    with client.stream("POST", "/chat", json={
        "kb_id": "kb_001", "question": "Q3 销售如何？", "history": [],
    }) as r:
        events = _read_sse_events(r)
    types = [e["type"] for e in events]
    assert "token" in types
    assert types[-1] == "done"
    tokens = [e["content"] for e in events if e["type"] == "token"]
    assert "".join(tokens) == "销售额下降"


def test_chat_emits_citations_with_filename_page_image_url(app_and_fakes):
    app, _, _ = app_and_fakes
    client = TestClient(app)
    with client.stream("POST", "/chat", json={
        "kb_id": "kb_001", "question": "Q3 销售如何？", "history": [],
    }) as r:
        events = _read_sse_events(r)
    cit_event = next(e for e in events if e["type"] == "citations")
    items = cit_event["items"]
    # 至少包含 doc_a / page 12 的来源
    assert any(i["filename"] == "report.pdf" and i["page"] == 12 for i in items)
    img_cit = next(i for i in items if i.get("image_url"))
    assert img_cit["image_url"] == "/static/doc_a/figures/fig_1.png"


def test_chat_passes_history_to_llm(app_and_fakes):
    app, qwen, _ = app_and_fakes
    client = TestClient(app)
    with client.stream("POST", "/chat", json={
        "kb_id": "kb_001",
        "question": "再说一次",
        "history": [
            {"role": "user", "content": "刚才说啥"},
            {"role": "assistant", "content": "销售下降"},
        ],
    }) as r:
        list(r.iter_lines())
    # qwen 收到的 messages 必须包含历史中的两条
    flat = json.dumps(qwen.last_messages, ensure_ascii=False)
    assert "刚才说啥" in flat
    assert "销售下降" in flat


def test_chat_handles_empty_retrieval(app_and_fakes):
    app, _, retriever = app_and_fakes
    retriever.text_hits = []
    retriever.image_hits = []
    retriever.bm25_ids = []
    client = TestClient(app)
    with client.stream("POST", "/chat", json={
        "kb_id": "kb_999", "question": "无结果", "history": [],
    }) as r:
        events = _read_sse_events(r)
    # 应该仍然返回完整流；citations 可以是空数组
    assert events[-1]["type"] == "done"
    cit = next((e for e in events if e["type"] == "citations"), None)
    assert cit is not None
    assert isinstance(cit["items"], list)
