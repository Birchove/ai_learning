"""Streamlit 前端 — 文件上传 + 多轮智能问答。

启动：
    streamlit run services/streamlit_app/app.py

依赖：upload-api 在 8001 端口、chat-api 在 8002 端口。
两个服务都用 .env 中配置的 STATIC_URL_PREFIX 提供图片。
"""

from __future__ import annotations

import json
import os
import time
from typing import Iterable, Iterator

import httpx
import streamlit as st


UPLOAD_URL = os.environ.get("UPLOAD_URL", "http://localhost:8001")
CHAT_URL = os.environ.get("CHAT_URL", "http://localhost:8002")
DEFAULT_KB = os.environ.get("DEFAULT_KB_ID", "kb_001")


st.set_page_config(page_title="多模态 RAG 问答", layout="wide")
st.title("多模态 RAG 问答")


with st.sidebar:
    st.header("知识库")
    kb_id = st.text_input("Knowledge Base ID", value=DEFAULT_KB)

    st.header("上传 PDF")
    uploaded = st.file_uploader("选择 PDF", type=["pdf"], accept_multiple_files=False)
    if uploaded is not None and st.button("上传", use_container_width=True):
        files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
        with st.spinner("上传中..."):
            r = httpx.post(
                f"{UPLOAD_URL}/upload/document",
                files=files, data={"kb_id": kb_id}, timeout=60.0,
            )
        if r.status_code == 200:
            body = r.json()
            st.success(f"已上传 {body['filename']}，doc_id={body['doc_id']}")
            st.session_state.setdefault("watching", []).append(body["doc_id"])
        else:
            st.error(f"上传失败：{r.status_code} {r.text}")

    # 解析进度轮询（极简，刷新一次拉一次）
    watching = st.session_state.get("watching", [])
    if watching:
        st.markdown("**解析状态**")
        for doc_id in list(watching):
            try:
                s = httpx.get(f"{UPLOAD_URL}/documents/{doc_id}/status", timeout=5.0).json()
                st.write(f"- `{doc_id}` → {s['status']}")
                if s["status"] in ("embedded", "failed"):
                    st.session_state["watching"].remove(doc_id)
            except Exception as e:
                st.write(f"- `{doc_id}` → 查询失败：{e}")
        if st.button("刷新状态", use_container_width=True):
            time.sleep(0.1)
            st.rerun()


# ---------- 聊天主区 ----------
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # [{role, content, citations?}]


def _stream_chat(kb_id: str, question: str, history: list) -> Iterator[dict]:
    payload = {"kb_id": kb_id, "question": question, "history": history}
    with httpx.Client(timeout=300.0) as client:
        with client.stream("POST", f"{CHAT_URL}/chat", json=payload) as r:
            for line in r.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                yield json.loads(line[len("data: "):])


# 渲染历史
for m in st.session_state["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        for cit in m.get("citations", []):
            cap = f"{cit['filename']} - p{cit['page']}"
            if cit.get("chapter"):
                cap += f" ({cit['chapter']})"
            if cit.get("image_url"):
                st.image(f"{CHAT_URL}{cit['image_url']}", caption=cap, width=320)
            else:
                st.caption(cap)


user_q = st.chat_input("问点什么...")
if user_q:
    # 当前轮 user 消息先入记录
    st.session_state["messages"].append({"role": "user", "content": user_q})
    with st.chat_message("user"):
        st.markdown(user_q)

    # 给 chat_api 的 history 不包含本轮 user 消息（chat_api 把它单独当 question）
    api_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state["messages"][:-1]
    ]

    with st.chat_message("assistant"):
        text_box = st.empty()
        cit_box = st.container()
        buf = ""
        citations: list[dict] = []
        try:
            for ev in _stream_chat(kb_id, user_q, api_history):
                if ev["type"] == "token":
                    buf += ev["content"]
                    text_box.markdown(buf)
                elif ev["type"] == "citations":
                    citations = ev["items"]
                elif ev["type"] == "done":
                    break
        except Exception as e:
            text_box.error(f"调用 chat-api 失败：{e}")

        with cit_box:
            for cit in citations:
                cap = f"{cit['filename']} - p{cit['page']}"
                if cit.get("chapter"):
                    cap += f" ({cit['chapter']})"
                if cit.get("image_url"):
                    st.image(f"{CHAT_URL}{cit['image_url']}", caption=cap, width=320)
                else:
                    st.caption(cap)

    st.session_state["messages"].append(
        {"role": "assistant", "content": buf, "citations": citations}
    )
