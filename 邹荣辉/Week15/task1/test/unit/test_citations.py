"""引用结构生成 — 把内部图片路径重写为 /static URL。"""

from pathlib import Path


def test_build_citation_from_text_chunk(tmp_path):
    from services.chat_api.citations import build_citation
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path, static_url_prefix="/static")
    cit = build_citation(
        modality="text", filename="report.pdf", page=12, chapter="3.2",
        image_path=None, sp=sp,
    )
    assert cit.filename == "report.pdf"
    assert cit.page == 12
    assert cit.image_url is None


def test_build_citation_from_image_chunk(tmp_path):
    from services.chat_api.citations import build_citation
    from libs.common.storage.paths import StoragePaths
    sp = StoragePaths(data_dir=tmp_path, static_url_prefix="/static")
    img = tmp_path / "parsed" / "doc_1" / "figures" / "fig_3.png"
    cit = build_citation(
        modality="image", filename="report.pdf", page=12, chapter=None,
        image_path=str(img), sp=sp,
    )
    assert cit.image_url == "/static/doc_1/figures/fig_3.png"


def test_dedup_citations_keeps_first_occurrence(tmp_path):
    from services.chat_api.citations import dedup_citations
    from libs.common.schemas.chat import Citation
    a = Citation(filename="r.pdf", page=12)
    b = Citation(filename="r.pdf", page=12, image_url="/static/x.png")
    c = Citation(filename="r.pdf", page=13)
    out = dedup_citations([a, b, c])
    # 同 (filename, page) 合并；image_url 优先非空
    assert len(out) == 2
    twelve = next(x for x in out if x.page == 12)
    assert twelve.image_url == "/static/x.png"
