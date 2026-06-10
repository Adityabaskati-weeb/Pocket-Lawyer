from __future__ import annotations

from pathlib import Path

from pocket_lawyer.intake.docling_text import (
    DOCLING_SUPPORTED_SUFFIXES,
    docling_is_available,
    extract_docling_document,
    get_docling_install_message,
)
from pocket_lawyer.intake.errors import (
    DoclingSupportMissing,
    IntakeError,
    UnsupportedFileType,
)
from pocket_lawyer.intake.models import (
    ExtractedBlock,
    ExtractedDocument,
    ExtractedPage,
)
from pocket_lawyer.intake.pdf_text import extract_pdf_pages


TEXT_SUFFIXES = {".txt", ".text", ".md"}


def extract_contract_document(filename: str, content: bytes) -> ExtractedDocument:
    suffix = Path(filename).suffix.lower()

    if suffix in TEXT_SUFFIXES:
        return build_text_document(
            decode_text(content),
            filename=filename,
            backend="utf8_text",
        )

    if suffix == ".pdf":
        return _extract_pdf_document(filename, content)

    if suffix in DOCLING_SUPPORTED_SUFFIXES:
        if not docling_is_available():
            raise DoclingSupportMissing(get_docling_install_message())

        return extract_docling_document(filename, content)

    raise UnsupportedFileType(_unsupported_file_message())


def extract_contract_text(filename: str, content: bytes) -> str:
    return extract_contract_document(filename, content).text


def build_text_document(
    text: str,
    *,
    filename: str = "Pasted contract",
    backend: str = "pasted_text",
) -> ExtractedDocument:
    cleaned = text.strip()
    if not cleaned:
        raise IntakeError("The uploaded file does not contain readable text.")

    block = ExtractedBlock(
        index=0,
        text=cleaned,
        char_start=0,
        char_end=len(cleaned),
        page_number=1,
        label="body",
    )
    page = ExtractedPage(
        number=1,
        text=cleaned,
        char_start=0,
        char_end=len(cleaned),
        block_indexes=[0],
    )
    return ExtractedDocument(
        filename=filename,
        text=cleaned,
        backend=backend,
        pages=[page],
        blocks=[block],
    )


def build_paged_document(
    filename: str,
    *,
    backend: str,
    page_texts: list[str],
    used_ocr: bool = False,
    ocr_engine: str | None = None,
    metadata: dict[str, object] | None = None,
) -> ExtractedDocument:
    cleaned_pages = [page.strip() for page in page_texts if page.strip()]
    if not cleaned_pages:
        raise IntakeError("The uploaded file does not contain readable text.")

    blocks: list[ExtractedBlock] = []
    pages: list[ExtractedPage] = []
    text_parts: list[str] = []
    cursor = 0

    for index, page_text in enumerate(cleaned_pages, start=1):
        if text_parts:
            text_parts.append("\n\n")
            cursor += 2

        page_start = cursor
        text_parts.append(page_text)
        cursor += len(page_text)
        page_end = cursor

        block_index = len(blocks)
        blocks.append(
            ExtractedBlock(
                index=block_index,
                text=page_text,
                char_start=page_start,
                char_end=page_end,
                page_number=index,
                label=f"page_{index}",
            )
        )
        pages.append(
            ExtractedPage(
                number=index,
                text=page_text,
                char_start=page_start,
                char_end=page_end,
                block_indexes=[block_index],
            )
        )

    return ExtractedDocument(
        filename=filename,
        text="".join(text_parts),
        backend=backend,
        pages=pages,
        blocks=blocks,
        used_ocr=used_ocr,
        ocr_engine=ocr_engine,
        metadata=dict(metadata or {}),
    )


def decode_text(content: bytes) -> str:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IntakeError("Text files must be UTF-8 encoded.") from exc

    text = text.strip()
    if not text:
        raise IntakeError("The uploaded file does not contain readable text.")

    return text


def _extract_pdf_document(filename: str, content: bytes) -> ExtractedDocument:
    try:
        pages = extract_pdf_pages(content)
    except IntakeError:
        if not docling_is_available():
            raise

        return extract_docling_document(filename, content, require_ocr=True)

    return build_paged_document(filename, backend="pypdf", page_texts=pages)


def _unsupported_file_message() -> str:
    return (
        "Only .txt, .md, and .pdf are supported by the base install. Install the "
        "optional Docling intake backend for .docx and image uploads."
    )
