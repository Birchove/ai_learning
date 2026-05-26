"""图片 + caption 配对 — 解析 markdown 中 ![alt](path) 与其周围文字。"""


def test_pair_caption_below_image():
    from services.parse_worker.image_chunker import pair_images_with_captions
    md = """正文段落。

![](figures/fig_1.png)

图1：销售趋势

下一段。"""
    pairs = pair_images_with_captions(md, base_dir="/data/parsed/doc_a")
    assert len(pairs) == 1
    assert pairs[0].image_path == "/data/parsed/doc_a/figures/fig_1.png"
    assert "图1" in pairs[0].caption


def test_pair_caption_above_image():
    from services.parse_worker.image_chunker import pair_images_with_captions
    md = """图2：产品分类

![](figures/fig_2.png)

正文。"""
    pairs = pair_images_with_captions(md, base_dir="/x")
    assert len(pairs) == 1
    assert "图2" in pairs[0].caption


def test_no_caption_when_neighbour_is_empty():
    from services.parse_worker.image_chunker import pair_images_with_captions
    md = "![](a.png)"
    pairs = pair_images_with_captions(md, base_dir="/x")
    assert len(pairs) == 1
    assert pairs[0].caption == ""


def test_multiple_images():
    from services.parse_worker.image_chunker import pair_images_with_captions
    md = """![](figures/a.png)

图A

![](figures/b.png)

图B"""
    pairs = pair_images_with_captions(md, base_dir="/x")
    assert {p.image_path for p in pairs} == {"/x/figures/a.png", "/x/figures/b.png"}
