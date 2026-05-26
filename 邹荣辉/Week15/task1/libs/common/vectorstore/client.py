"""Milvus 客户端 — 连接管理 + 两个 collection 的封装。"""

from typing import List, Optional

from pymilvus import Collection, connections, utility

from libs.common.vectorstore.collections import (
    BGE_DIM, CLIP_DIM,
    IMAGE_COLLECTION_NAME, TEXT_COLLECTION_NAME,
    build_image_schema, build_text_schema,
)


def connect(host: str, port: int, alias: str = "default") -> None:
    connections.connect(alias=alias, host=host, port=str(port))


def disconnect(alias: str = "default") -> None:
    connections.disconnect(alias)


def ensure_collections() -> None:
    for name, schema, dim in [
        (TEXT_COLLECTION_NAME, build_text_schema(), BGE_DIM),
        (IMAGE_COLLECTION_NAME, build_image_schema(), CLIP_DIM),
    ]:
        if not utility.has_collection(name):
            Collection(name=name, schema=schema)
        col = Collection(name)
        if not col.has_index():
            col.create_index(
                field_name="embedding",
                index_params={
                    "index_type": "IVF_FLAT",
                    "metric_type": "IP",
                    "params": {"nlist": 128},
                },
            )
        col.load()


def get_text_collection() -> Collection:
    return Collection(TEXT_COLLECTION_NAME)


def get_image_collection() -> Collection:
    return Collection(IMAGE_COLLECTION_NAME)
