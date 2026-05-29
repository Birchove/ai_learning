"""chat_api 启动入口 — 把真实模型 / Milvus / BM25 接好后启动 FastAPI。

用法：
    uvicorn services.chat_api.entrypoint:app --port 8002
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.staticfiles import StaticFiles

from libs.common.config import Settings
from libs.common.db.engine import init_schema, make_engine, make_sessionmaker
from libs.common.db.models import Document
from libs.common.models.bge import BGEEncoder
from libs.common.models.clip import ChineseCLIPEncoder
from libs.common.models.qwen_vl import QwenVLGenerator
from libs.common.models.reranker import BGEReranker
from libs.common.storage.paths import StoragePaths
from libs.common.vectorstore import client as vs_client
from libs.common.vectorstore import ops as vs_ops
from services.chat_api.main import build_app
from services.chat_api.retrieval.bm25 import BM25Index


class _MilvusRetriever:
    def __init__(self, bm25: BM25Index) -> None:
        self.bm25 = bm25

    def text_search(self, kb_id, qv, top_k):
        return vs_ops.search_text(kb_id, qv.tolist() if hasattr(qv, "tolist") else qv, top_k)

    def image_search(self, kb_id, qv, top_k):
        return vs_ops.search_image(kb_id, qv.tolist() if hasattr(qv, "tolist") else qv, top_k)

    def bm25_search(self, kb_id, query, top_k):
        return self.bm25.search(kb_id, query, top_k)


def _bootstrap():
    s = Settings()
    engine = make_engine(s.sqlite_path)
    init_schema(engine)
    SessionLocal = make_sessionmaker(engine)

    # filename 映射 — chat_api 启动时一次性读 SQLite
    with SessionLocal() as session:
        filename_lookup = {d.id: d.filename for d in session.query(Document).all()}

    sp = StoragePaths(data_dir=Path(s.data_dir), static_url_prefix=s.static_url_prefix)
    sp.ensure_base_dirs()

    vs_client.connect(s.milvus_host, s.milvus_port)
    vs_client.ensure_collections()

    bge = BGEEncoder(s.bge_model_path, device=s.torch_device)
    clip = ChineseCLIPEncoder(s.clip_model_path, device=s.torch_device)
    reranker = BGEReranker(s.reranker_model_path, device=s.torch_device)
    qwen = QwenVLGenerator(s.qwen_vl_model_path, device=s.torch_device, dtype=s.qwen_vl_dtype)

    bm25 = BM25Index()
    # v1：BM25 索引启动时不预热（首次问答前先空跑），后续可加从 Milvus dump 重建
    retriever = _MilvusRetriever(bm25)

    app = build_app(
        bge=bge, clip=clip, reranker=reranker, qwen=qwen,
        retriever=retriever, sp=sp, filename_lookup=filename_lookup,
        bm25_top_k=s.bm25_top_k, bge_top_k=s.bge_top_k,
        clip_top_k=s.clip_top_k, rerank_top_k=s.rerank_top_k,
        max_images=s.qwen_vl_max_images,
    )

    # 静态目录：把 parsed/ 挂到 /static
    app.mount(
        s.static_url_prefix.rstrip("/") or "/static",
        StaticFiles(directory=str(sp.parsed_root)),
        name="static",
    )
    return app


app = _bootstrap()
