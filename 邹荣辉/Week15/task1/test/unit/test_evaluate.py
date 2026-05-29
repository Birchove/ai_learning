"""评测脚本 — 实现 README 锁定的三项打分。

测试集格式：JSONL，每行
    {"question": ..., "expected_filenames": [...], "expected_pages": [...], "expected_answer": ...}

打分：
- 页面匹配度 (0.25)：预测引用中的 page 与 expected_pages 有交集
- 文件名匹配度 (0.25)：预测引用中的 filename 与 expected_filenames 有交集
- 答案内容相似度 (0.5)：字符 Jaccard
"""


def test_jaccard_identical_strings_is_1():
    from scripts.evaluate import jaccard_chars
    assert jaccard_chars("销售下降", "销售下降") == 1.0


def test_jaccard_no_overlap_is_0():
    from scripts.evaluate import jaccard_chars
    assert jaccard_chars("abc", "xyz") == 0.0


def test_jaccard_partial_overlap():
    from scripts.evaluate import jaccard_chars
    # 交集 {a,b}=2, 并集 {a,b,c,d}=4, → 0.5
    assert jaccard_chars("ab", "abcd") == 0.5


def test_score_full_marks_when_everything_matches():
    from scripts.evaluate import score_one
    s = score_one(
        predicted_answer="销售下降",
        predicted_filenames=["report.pdf"],
        predicted_pages=[12],
        expected_answer="销售下降",
        expected_filenames=["report.pdf"],
        expected_pages=[12],
    )
    assert s["page"] == 0.25
    assert s["filename"] == 0.25
    assert s["answer"] == 0.5
    assert s["total"] == 1.0


def test_score_zero_when_nothing_matches():
    from scripts.evaluate import score_one
    s = score_one(
        predicted_answer="abc",
        predicted_filenames=["other.pdf"],
        predicted_pages=[99],
        expected_answer="xyz",
        expected_filenames=["report.pdf"],
        expected_pages=[12],
    )
    assert s["total"] == 0.0


def test_score_partial_when_only_filename_matches():
    from scripts.evaluate import score_one
    s = score_one(
        predicted_answer="abc",
        predicted_filenames=["report.pdf"],
        predicted_pages=[99],
        expected_answer="xyz",
        expected_filenames=["report.pdf"],
        expected_pages=[12],
    )
    assert s["page"] == 0.0
    assert s["filename"] == 0.25
    assert s["answer"] == 0.0
    assert s["total"] == 0.25
