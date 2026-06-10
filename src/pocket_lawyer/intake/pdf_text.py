from __future__ import annotations

from io import BytesIO

from pocket_lawyer.intake.errors import IntakeError, PDFSupportMissing


def extract_pdf_pages(content: bytes) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PDFSupportMissing(
            "PDF support requires pypdf. Install project dependencies with "
            "python -m pip install -e ."
        ) from exc

    try:
        reader = PdfReader(BytesIO(content))
        page_text = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise IntakeError("The uploaded PDF could not be parsed.") from exc

    pages = [text for text in page_text if text]
    if not pages:
        raise IntakeError(
            "No readable text was found in this PDF. Try pasting the contract text."
        )

    return pages


def extract_pdf_text(content: bytes) -> str:
    return "\n\n".join(extract_pdf_pages(content)).strip()
