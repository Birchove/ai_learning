"""MinerU 文档解析 wrapper。

接口契约：
    parser = MineruParser(model_path)
    result = parser.parse(pdf_path, output_dir)
    # result: ParsedDocument(markdown_path, figures_dir, page_count)

v1 通过 magic-pdf 命令行 / Python API 调用。
真实集成时可能需要按 MinerU 实际 API 调整 — 这里给一个占位实现。
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass
class ParsedDocument:
    markdown_path: Path
    figures_dir: Path
    page_count: int


class MineruParser:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    def parse(self, pdf_path: Path, output_dir: Path) -> ParsedDocument:
        output_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["magic-pdf", "-p", str(pdf_path), "-o", str(output_dir), "-m", "auto"],
            check=True,
            env={"MINERU_MODEL_SOURCE": self.model_path},
        )
        markdown_path = next(output_dir.rglob("*.md"))
        figures_dir = markdown_path.parent / "images"
        page_count = self._count_pages(pdf_path)
        return ParsedDocument(
            markdown_path=markdown_path,
            figures_dir=figures_dir,
            page_count=page_count,
        )

    @staticmethod
    def _count_pages(pdf_path: Path) -> int:
        import pypdf
        return len(pypdf.PdfReader(str(pdf_path)).pages)
