from __future__ import annotations

from io import BytesIO
from pathlib import Path


class IntakeError(ValueError):
    """Raised when uploaded contract content cannot be read."""


class UnsupportedFileType(IntakeError):
    """Raised when a file type is not supported by the MVP intake layer."""


class PDFSupportMissing(IntakeError):
    """Raised when PDF parsing is requested without a local parser installed."""


def extract_contract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix in {".txt", ".text", ".md"}:
        return _decode_text(content)

    if suffix == ".pdf":
        return extract_pdf_text(content)

    raise UnsupportedFileType("Only .txt, .md, and .pdf files are supported.")


def extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFSupportMissing(
            "PDF support requires pypdf. Install project dependencies with "
            "python -m pip install -e ."
        ) from exc

    reader = PdfReader(BytesIO(content))
    page_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(part.strip() for part in page_text if part.strip()).strip()

    if not text:
        raise IntakeError(
            "No readable text was found in this PDF. Try pasting the contract text."
        )

    return text


def _decode_text(content: bytes) -> str:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IntakeError("Text files must be UTF-8 encoded.") from exc

    text = text.strip()
    if not text:
        raise IntakeError("The uploaded file does not contain readable text.")

    return text
