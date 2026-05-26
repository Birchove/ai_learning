"""chat_api FastAPI 应用 — 全部依赖外部注入，方便测试与运行环境替换。"""

from typing import Any, Dict, List, Mapping, Protocol

from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

from libs.common.schemas.chat import ChatRequest, Citation
from libs.common.storage.paths import StoragePaths
from services.chat_api.citations import build_citation, dedup_citations
from services.chat_api.retrieval.fusion import rrf_fuse


class _Retriever(Protocol):
    def text_search(self, kb_id: str, qv, top_k: int) -> List[Dict[str, Any]]: ...
    def image_search(self, kb_id: str, qv, top_k: int) -> List[Dict[str, Any]]: ...
    def bm25_search(self, kb_id: str, query: str, top_k: int) -> List[str]: ...


def build_app(
    *,
    bge, clip, reranker, qwen,
    retriever: _Retriever,
    sp: StoragePaths,
    filename_lookup: Mapping[str, str],
    bm25_top_k: int = 100,
    bge_top_k: int = 100,
    clip_top_k: int = 50,
    rerank_top_k: int = 10,
    max_images: int = 3,
) -> FastAPI:
    app = FastAPI(title="chat-api")

    @app.post("/chat")
    def chat(req: ChatRequest):
        # 1) 三路召回
        q_text_vec = bge.encode([req.question])[0]
        q_image_vec = clip.encode_text([req.question])[0]
        text_hits = retriever.text_search(req.kb_id, q_text_vec, bge_top_k)
        image_hits = retriever.image_search(req.kb_id, q_image_vec, clip_top_k)
        bm25_ids = retriever.bm25_search(req.kb_id, req.question, bm25_top_k)

        # 2) RRF 融合（按 chunk id 排序）
        text_ids = [h["id"] for h in text_hits]
        image_ids = [h["id"] for h in image_hits]
        fused_ids = rrf_fuse([bm25_ids, text_ids, image_ids])

        # 3) 重排
        id_to_hit = {h["id"]: h for h in text_hits + image_hits}
        rerank_inputs = [
            (id_to_hit[i].get("content") or id_to_hit[i].get("caption") or "")
            for i in fused_ids if i in id_to_hit
        ]
        if rerank_inputs:
            scores = reranker.rerank(req.question, rerank_inputs)
            indices = sorted(
                range(len(rerank_inputs)),
                key=lambda j: float(scores[j]),
                reverse=True,
            )[:rerank_top_k]
        else:
            indices = []

        ranked_ids = [fused_ids[j] for j in indices]
        topk = [id_to_hit[i] for i in ranked_ids]

        # 4) 拼装 LLM messages — 历史 + 当前问题（带文本上下文 + 至多 N 张图）
        text_ctx = "\n\n".join(
            f"[来源 {h['doc_id']} p{h['page']}] {h.get('content') or h.get('caption', '')}"
            for h in topk
        )
        image_paths = [h["image_path"] for h in topk if "image_path" in h][:max_images]

        messages: List[Dict[str, Any]] = []
        for m in req.history:
            messages.append({"role": m.role, "content": [{"type": "text", "text": m.content}]})
        user_content: List[Dict[str, Any]] = [{"type": "text", "text": text_ctx}]
        for ip in image_paths:
            user_content.append({"type": "image", "image": ip})
        user_content.append({"type": "text", "text": req.question})
        messages.append({"role": "user", "content": user_content})

        # 5) 引用结构（在生成前算好，最后再吐）
        citations: List[Citation] = []
        for h in topk:
            modality = "image" if "image_path" in h else "text"
            filename = filename_lookup.get(h["doc_id"], h["doc_id"])
            citations.append(
                build_citation(
                    modality=modality, filename=filename,
                    page=int(h["page"]), chapter=None,
                    image_path=h.get("image_path"), sp=sp,
                )
            )
        citations = dedup_citations(citations)

        # 6) SSE 流：先吐 token，再吐 citations，再 done
        def event_stream():
            import json as _json
            for tok in qwen.stream_generate(messages):
                yield {"data": _json.dumps({"type": "token", "content": tok}, ensure_ascii=False)}
            yield {
                "data": _json.dumps(
                    {"type": "citations", "items": [c.model_dump() for c in citations]},
                    ensure_ascii=False,
                )
            }
            yield {"data": _json.dumps({"type": "done"})}

        return EventSourceResponse(event_stream(), ping=15, send_timeout=None)

    return app
