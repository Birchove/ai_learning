"""统一的本地路径 / URL 计算 — 不连真实 FS。"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoragePaths:
    data_dir: Path
    static_url_prefix: str = "/static"

    @property
    def pdf_dir(self) -> Path:
        return self.data_dir / "pdfs"

    @property
    def parsed_root(self) -> Path:
        return self.data_dir / "parsed"

    def pdf_path(self, doc_id: str) -> Path:
        return self.pdf_dir / f"{doc_id}.pdf"

    def parsed_dir(self, doc_id: str) -> Path:
        return self.parsed_root / doc_id

    def markdown_path(self, doc_id: str) -> Path:
        return self.parsed_dir(doc_id) / "content.md"

    def figures_dir(self, doc_id: str) -> Path:
        return self.parsed_dir(doc_id) / "figures"

    def to_static_url(self, internal: Path) -> str:
        try:
            rel = internal.resolve().relative_to(self.parsed_root.resolve())
        except ValueError as e:
            raise ValueError(f"path {internal} outside parsed root") from e
        return f"{self.static_url_prefix.rstrip('/')}/{rel.as_posix()}"

    def ensure_base_dirs(self) -> None:
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_root.mkdir(parents=True, exist_ok=True)
