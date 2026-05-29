"""Milvus collection schema 定义。

两个 collection 维度不同，必须分开。具体维度由各自模型决定：
- text_chunks  : BGE      → BGE_DIM (small=512, large=1024)
- image_chunks : Chinese-CLIP → CLIP_DIM (base=512, large=768)

维度通过环境变量覆盖，由 .env 配置。
两个 collection 都用 kb_id 作 partition_key，实现知识库级别隔离。
"""

import os

from pymilvus import CollectionSchema, DataType, FieldSchema

TEXT_COLLECTION_NAME = "text_chunks"
IMAGE_COLLECTION_NAME = "image_chunks"

# 默认值对应 BGE-small / Chinese-CLIP-base（用户当前 .env 的选择）；
# 换成 BGE-large 设 BGE_DIM=1024，换成 Chinese-CLIP-large 设 CLIP_DIM=768。
BGE_DIM = int(os.environ.get("BGE_DIM", "512"))
CLIP_DIM = int(os.environ.get("CLIP_DIM", "512"))

_ID_MAX = 64
_KB_ID_MAX = 64
_DOC_ID_MAX = 64
_MODALITY_MAX = 16
_PATH_MAX = 1024
_CONTENT_MAX = 4096
_CAPTION_MAX = 1024


def _common_meta_fields() -> list[FieldSchema]:
    return [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=_ID_MAX, is_primary=True),
        FieldSchema(
            name="kb_id",
            dtype=DataType.VARCHAR,
            max_length=_KB_ID_MAX,
            is_partition_key=True,
        ),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=_DOC_ID_MAX),
        FieldSchema(name="page", dtype=DataType.INT32),
        FieldSchema(name="chunk_idx", dtype=DataType.INT32),
        FieldSchema(name="modality", dtype=DataType.VARCHAR, max_length=_MODALITY_MAX),
    ]


def build_text_schema() -> CollectionSchema:
    fields = _common_meta_fields() + [
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=_CONTENT_MAX),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=BGE_DIM),
    ]
    return CollectionSchema(fields=fields, description="Text chunks (BGE)")


def build_image_schema() -> CollectionSchema:
    fields = _common_meta_fields() + [
        FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=_PATH_MAX),
        FieldSchema(name="caption", dtype=DataType.VARCHAR, max_length=_CAPTION_MAX),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=CLIP_DIM),
    ]
    return CollectionSchema(fields=fields, description="Image chunks (Chinese-CLIP)")

_ID_MAX = 64
_KB_ID_MAX = 64
_DOC_ID_MAX = 64
_MODALITY_MAX = 16
_PATH_MAX = 1024
_CONTENT_MAX = 4096
_CAPTION_MAX = 1024


def _common_meta_fields() -> list[FieldSchema]:
    return [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=_ID_MAX, is_primary=True),
        FieldSchema(
            name="kb_id",
            dtype=DataType.VARCHAR,
            max_length=_KB_ID_MAX,
            is_partition_key=True,
        ),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=_DOC_ID_MAX),
        FieldSchema(name="page", dtype=DataType.INT32),
        FieldSchema(name="chunk_idx", dtype=DataType.INT32),
        FieldSchema(name="modality", dtype=DataType.VARCHAR, max_length=_MODALITY_MAX),
    ]


def build_text_schema() -> CollectionSchema:
    fields = _common_meta_fields() + [
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=_CONTENT_MAX),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=BGE_DIM),
    ]
    return CollectionSchema(fields=fields, description="Text chunks (BGE)")


def build_image_schema() -> CollectionSchema:
    fields = _common_meta_fields() + [
        FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=_PATH_MAX),
        FieldSchema(name="caption", dtype=DataType.VARCHAR, max_length=_CAPTION_MAX),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=CLIP_DIM),
    ]
    return CollectionSchema(fields=fields, description="Image chunks (Chinese-CLIP)")
