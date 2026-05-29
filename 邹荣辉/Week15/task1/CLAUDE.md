# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repo currently holds only the project spec (`README.md`, in Chinese) and `demo.png`. No source code, dependency manifests, tests, or build tooling exist yet — there are no commands to build, lint, or run anything until the implementation is started.

When the user asks to begin implementation, treat the README as the authoritative design document and reply in Chinese to match the user's working language.

## Intended architecture (from README)

A multimodal RAG chatbot over a knowledge base of image-rich PDFs. The README locks in three independent services plus shared infrastructure — preserve this split when implementing:

- **`web_page_upload`** — FastAPI producer (~10 concurrent uploads). Saves uploaded PDFs locally and publishes a parse task to Kafka. `POST /upload/document` is knowledge-base-scoped.
- **`offline_process_worker`** — Kafka consumer. Calls MinerU to convert PDFs → Markdown + extracted image files, chunks the markdown, embeds chunks and images, writes vectors to Milvus.
- **`web_page_chat`** — FastAPI RAG endpoint. `POST /chat` takes `{question, knowledge_base_id}`, runs three-way retrieval, reranks, calls Qwen-VL with the retrieved context, and streams the answer. Image references in the answer must be rewritten from internal storage paths to externally-servable URLs.

### Why this shape (decisions the README explicitly justifies)

- **Kafka between upload and parse** — MinerU is GPU-bound and takes ~1 minute per file, so it cannot run inline with an HTTP upload. Upload concurrency and parse concurrency are decoupled on purpose. Do not collapse this into a synchronous call.
- **MinerU for parsing, not Qwen-VL or pymupdf** — pymupdf/pdfplumber lose layout and can't interpret figures; Qwen-VL understands documents but doesn't extract images as files. MinerU is the only listed option that yields Markdown + image files suitable for chunking and embedding. (DeepSeek-OCR was considered earlier but the current spec picks MinerU.)
- **CLIP at retrieval, Qwen-VL at generation** — embeddings happen offline / at query time; Qwen-VL only runs over the already-retrieved top-K context.
- **Milvus + SQLite** — vector search lives in Milvus; document/knowledge-base/parse-task metadata lives in SQLite. Local filesystem is the storage for raw PDFs and parsed Markdown/images (no OSS).

## Concrete parameters locked in by the spec

Treat these as defaults — do not silently change them:

- **Chunking**: recursive split on natural semantic boundaries, `chunk_size=500`, `overlap=50`.
- **Image chunks**: image + its surrounding caption are embedded together, not separately.
- **Three-way retrieval** with these top-K: BM25 full-text top-100, BGE dense vector top-100, CLIP cross-modal top-50. Fuse with **RRF**, then run a **cross-encoder reranker**, return **top-10** to the LLM.
- **CLIP variant**: **Chinese-CLIP** (the original CLIP is too weak for Chinese).
- **Generation context**: image + caption fed to Qwen-VL, **4k token** budget.
- **`/chat`** must be **streaming**, support **multi-turn**, return images as **URLs**, and cite source down to **document + chapter** (and ideally page/figure to satisfy the evaluator).
- **Milvus schema**: every vector carries `doc_id`, `page`, `chunk_idx`, `modality ∈ {text, image}`, `kb_id`. `kb_id` filtering is how `/chat` scopes to a knowledge base.
- **Models are all local** — never call online APIs. Every model (Qwen-VL, Chinese-CLIP, BGE, MinerU, reranker) needs a configurable local path; the user fills these in manually.

## Answer requirements (drives evaluation)

The evaluator scores each answer on three axes — page match (0.25), filename match (0.25), and Jaccard answer similarity (0.5). The response payload therefore needs structured `filename` and `page` fields alongside the prose, not just inline citations.

## Inconsistencies in the spec — flag, don't silently resolve

- The tech-stack tagline at line 38 lists **Elasticsearch** and **MySQL**, but the detailed middleware section only specifies **SQLite + Milvus**. BM25 is in the retrieval plan with no backend named. Confirm with the user whether BM25 runs via ES, Milvus's built-in BM25, or a Python library before picking.
- The tagline also lists **vLLM**, but the body never says what it serves. Likely for hosting Qwen-VL locally — confirm.
- Earlier README drafts mentioned `权限管理` (permissions/auth); the current version drops it. Confirm whether multi-tenant auth is out of scope before skipping it.

## Open design questions the README still leaves unresolved

When implementing, expect to make calls on these — confirm with the user rather than guessing:

- How the worker reports parse-task status back so `/chat` knows a document is ready and `/upload` clients can poll progress.
- The exact mechanism for rewriting internal image paths to externally-servable URLs (static file server vs. signed URLs vs. reverse-proxied path).
- Where multi-turn `/chat` conversation history is stored (SQLite? in-memory? client-passed?).
- Failure handling for MinerU parse: retries, dead-letter topic, partial-success behavior.
