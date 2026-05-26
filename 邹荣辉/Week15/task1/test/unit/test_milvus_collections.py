"""Milvus collection schema 单元测试 —— 不连真实 Milvus，只验证 schema 结构。"""

from pymilvus import DataType


def _by_name(schema):
    return {f.name: f for f in schema.fields}


def test_text_collection_schema_has_required_fields():
    from libs.common.vectorstore.collections import build_text_schema

    schema = build_text_schema()
    fields = _by_name(schema)

    assert set(fields) == {
        "id", "kb_id", "doc_id", "page", "chunk_idx", "modality", "content", "embedding"
    }


def test_text_collection_uses_pk_id_and_partitions_by_kb():
    from libs.common.vectorstore.collections import build_text_schema

    fields = _by_name(build_text_schema())
    assert fields["id"].is_primary is True
    assert fields["kb_id"].is_partition_key is True
    assert fields["embedding"].dtype == DataType.FLOAT_VECTOR


def test_text_embedding_dim_matches_configured_bge():
    """BGE 维度由 BGE_DIM 控制（small=512, large=1024）。"""
    from libs.common.vectorstore.collections import BGE_DIM, build_text_schema

    fields = _by_name(build_text_schema())
    assert fields["embedding"].params["dim"] == BGE_DIM
    assert BGE_DIM in (512, 768, 1024)


def test_image_collection_schema_has_required_fields():
    from libs.common.vectorstore.collections import build_image_schema

    fields = _by_name(build_image_schema())

    assert set(fields) == {
        "id", "kb_id", "doc_id", "page", "chunk_idx", "modality",
        "image_path", "caption", "embedding",
    }


def test_image_collection_uses_pk_id_and_partitions_by_kb():
    from libs.common.vectorstore.collections import build_image_schema

    fields = _by_name(build_image_schema())
    assert fields["id"].is_primary is True
    assert fields["kb_id"].is_partition_key is True
    assert fields["embedding"].dtype == DataType.FLOAT_VECTOR


def test_image_embedding_dim_matches_configured_clip():
    """Chinese-CLIP 维度由 CLIP_DIM 控制（base=512, large=768）。"""
    from libs.common.vectorstore.collections import CLIP_DIM, build_image_schema

    fields = _by_name(build_image_schema())
    assert fields["embedding"].params["dim"] == CLIP_DIM
    assert CLIP_DIM in (512, 768)


def test_collection_names_are_exposed_as_constants():
    """名称是配置契约，外部代码会按它创建 / 检索，必须稳定。"""
    from libs.common.vectorstore.collections import (
        TEXT_COLLECTION_NAME, IMAGE_COLLECTION_NAME,
    )
    assert TEXT_COLLECTION_NAME == "text_chunks"
    assert IMAGE_COLLECTION_NAME == "image_chunks"
