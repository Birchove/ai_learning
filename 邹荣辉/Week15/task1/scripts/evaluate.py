"""评测：页/文件名/Jaccard 三项 + 全集合跑分。

用法：
    python scripts/evaluate.py --testset eval/testset.jsonl --chat-url http://localhost:8002

输出：每题分数 + 总分。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def jaccard_chars(a: str, b: str) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    union = sa | sb
    if not union:
        return 0.0
    return len(sa & sb) / len(union)


def score_one(
    *, predicted_answer: str,
    predicted_filenames: Iterable[str],
    predicted_pages: Iterable[int],
    expected_answer: str,
    expected_filenames: Iterable[str],
    expected_pages: Iterable[int],
) -> dict:
    pf = set(predicted_filenames)
    ef = set(expected_filenames)
    pp = set(predicted_pages)
    ep = set(expected_pages)
    page = 0.25 if pp & ep else 0.0
    filename = 0.25 if pf & ef else 0.0
    answer = 0.5 * jaccard_chars(predicted_answer, expected_answer)
    return {"page": page, "filename": filename, "answer": answer,
            "total": page + filename + answer}


def _call_chat(chat_url: str, kb_id: str, question: str) -> dict:
    """SSE 客户端：调 chat_api，把 token 拼起来 + 抓 citations。"""
    import httpx
    answer_parts: List[str] = []
    filenames: List[str] = []
    pages: List[int] = []
    with httpx.Client(timeout=120.0) as client:
        with client.stream(
            "POST", f"{chat_url.rstrip('/')}/chat",
            json={"kb_id": kb_id, "question": question, "history": []},
        ) as r:
            for line in r.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                event = json.loads(line[len("data: "):])
                if event["type"] == "token":
                    answer_parts.append(event["content"])
                elif event["type"] == "citations":
                    for c in event["items"]:
                        filenames.append(c["filename"])
                        pages.append(int(c["page"]))
                elif event["type"] == "done":
                    break
    return {"answer": "".join(answer_parts), "filenames": filenames, "pages": pages}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--testset", required=True)
    ap.add_argument("--chat-url", default="http://localhost:8002")
    ap.add_argument("--kb-id", default="kb_001")
    args = ap.parse_args()

    items = [json.loads(l) for l in Path(args.testset).read_text(encoding="utf-8").splitlines() if l.strip()]
    total = 0.0
    for i, q in enumerate(items, 1):
        pred = _call_chat(args.chat_url, args.kb_id, q["question"])
        s = score_one(
            predicted_answer=pred["answer"],
            predicted_filenames=pred["filenames"],
            predicted_pages=pred["pages"],
            expected_answer=q["expected_answer"],
            expected_filenames=q["expected_filenames"],
            expected_pages=q["expected_pages"],
        )
        total += s["total"]
        print(f"[{i}/{len(items)}] page={s['page']:.2f} file={s['filename']:.2f} ans={s['answer']:.2f} → {s['total']:.2f}")
    avg = total / len(items) if items else 0.0
    print(f"\nAverage score: {avg:.4f} ({total:.2f}/{len(items)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
