"""初始化 Milvus：创建 text_chunks / image_chunks 两个 collection（幂等）。

用法：
    python scripts/init_milvus.py

读取 MILVUS_HOST、MILVUS_PORT 环境变量，缺省 localhost:19530。
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pymilvus import Collection, CollectionSchema, connections, utility

from libs.common.vectorstore.collections import (
    IMAGE_COLLECTION_NAME,
    TEXT_COLLECTION_NAME,
    build_image_schema,
    build_text_schema,
)


def _ensure_collection(name: str, schema: CollectionSchema) -> None:
    if utility.has_collection(name):
        print(f"[init_milvus] {name} already exists, skip")
        return
    Collection(name=name, schema=schema)
    print(f"[init_milvus] created collection {name}")


def main() -> None:
    host = os.environ.get("MILVUS_HOST", "localhost")
    port = os.environ.get("MILVUS_PORT", "19530")
    connections.connect(alias="default", host=host, port=port)

    _ensure_collection(TEXT_COLLECTION_NAME, build_text_schema())
    _ensure_collection(IMAGE_COLLECTION_NAME, build_image_schema())

    print("[init_milvus] done")


if __name__ == "__main__":
    main()
