"""存储路径计算 — 纯函数。"""

from pathlib import Path


def test_pdf_path_uses_data_pdfs(tmp_path):
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path)
    assert sp.pdf_path("doc_1") == tmp_path / "pdfs" / "doc_1.pdf"


def test_parsed_dir_segregates_per_doc(tmp_path):
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path)
    assert sp.parsed_dir("doc_1") == tmp_path / "parsed" / "doc_1"


def test_markdown_path_inside_parsed_dir(tmp_path):
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path)
    assert sp.markdown_path("doc_1") == tmp_path / "parsed" / "doc_1" / "content.md"


def test_figures_dir_inside_parsed_dir(tmp_path):
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path)
    assert sp.figures_dir("doc_1") == tmp_path / "parsed" / "doc_1" / "figures"


def test_internal_to_static_url_rewrites_under_parsed(tmp_path):
    """图片本地路径 → /static URL — 这是 chat_api 的关键一步。"""
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path, static_url_prefix="/static")
    internal = tmp_path / "parsed" / "doc_1" / "figures" / "fig_3.png"
    assert sp.to_static_url(internal) == "/static/doc_1/figures/fig_3.png"


def test_to_static_url_rejects_path_outside_parsed(tmp_path):
    """安全：不允许把任意本地路径暴露成 URL。"""
    import pytest
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path, static_url_prefix="/static")
    with pytest.raises(ValueError):
        sp.to_static_url(Path("/etc/passwd"))


def test_ensure_dirs_creates_pdf_and_parsed(tmp_path):
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path)
    sp.ensure_base_dirs()
    assert (tmp_path / "pdfs").is_dir()
    assert (tmp_path / "parsed").is_dir()
