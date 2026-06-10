from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SourceBounds:
    left: float
    top: float
    right: float
    bottom: float
    unit: str = "pt"

    def to_dict(self) -> dict[str, float | str]:
        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "unit": self.unit,
        }


@dataclass(frozen=True, slots=True)
class ExtractedBlock:
    index: int
    text: str
    char_start: int
    char_end: int
    page_number: int | None = None
    label: str | None = None
    bounds: SourceBounds | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "text": self.text,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "page_number": self.page_number,
            "label": self.label,
            "bounds": self.bounds.to_dict() if self.bounds else None,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    number: int
    text: str
    char_start: int
    char_end: int
    block_indexes: list[int]
    width: float | None = None
    height: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "number": self.number,
            "text": self.text,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "block_indexes": list(self.block_indexes),
            "width": self.width,
            "height": self.height,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ExtractedDocument:
    filename: str
    text: str
    backend: str
    pages: list[ExtractedPage]
    blocks: list[ExtractedBlock]
    used_ocr: bool = False
    ocr_engine: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "filename": self.filename,
            "text": self.text,
            "backend": self.backend,
            "pages": [page.to_dict() for page in self.pages],
            "blocks": [block.to_dict() for block in self.blocks],
            "used_ocr": self.used_ocr,
            "ocr_engine": self.ocr_engine,
            "metadata": dict(self.metadata),
        }
