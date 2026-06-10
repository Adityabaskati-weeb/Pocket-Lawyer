from __future__ import annotations

import importlib.util

import pytest

import pocket_lawyer.intake.extract as intake_extract
from pocket_lawyer.intake import (
    DoclingArtifactsMissing,
    DoclingSupportMissing,
    IntakeError,
    OCRSupportMissing,
    UnsupportedFileType,
    extract_contract_document,
    extract_contract_text,
    extract_pdf_text,
)


def test_extracts_utf8_text_file() -> None:
    result = extract_contract_document(
        "contract.txt",
        "Both parties may terminate with 30 days notice.".encode("utf-8"),
    )

    assert result.text == "Both parties may terminate with 30 days notice."
    assert result.backend == "utf8_text"
    assert result.pages[0].number == 1
    assert result.blocks[0].char_start == 0
    assert result.blocks[0].char_end == len(result.text)


def test_rejects_unsupported_file_type() -> None:
    with pytest.raises(UnsupportedFileType):
        extract_contract_text("contract.rtf", b"not supported yet")


def test_docx_requires_docling_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(intake_extract, "docling_is_available", lambda: False)

    with pytest.raises(DoclingSupportMissing):
        extract_contract_text("contract.docx", b"not supported without docling")


def test_docx_uses_docling_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(intake_extract, "docling_is_available", lambda: True)
    monkeypatch.setattr(
        intake_extract,
        "extract_docling_document",
        lambda *_args, **_kwargs: intake_extract.build_text_document(
            "docling text",
            filename="contract.docx",
            backend="docling",
        ),
    )

    result = extract_contract_document("contract.docx", b"binary")

    assert result.text == "docling text"
    assert result.backend == "docling"


def test_rejects_empty_text_file() -> None:
    with pytest.raises(IntakeError):
        extract_contract_text("contract.txt", b"   ")


def test_pdf_falls_back_to_docling_when_native_text_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_pdf_extract(content: bytes) -> list[str]:
        raise IntakeError("No readable text was found in this PDF.")

    monkeypatch.setattr(intake_extract, "extract_pdf_pages", fake_pdf_extract)
    monkeypatch.setattr(intake_extract, "docling_is_available", lambda: True)
    monkeypatch.setattr(
        intake_extract,
        "extract_docling_document",
        lambda *_args, **_kwargs: intake_extract.build_text_document(
            "OCR fallback",
            filename="scan.pdf",
            backend="docling",
        ),
    )

    result = extract_contract_document("scan.pdf", b"%PDF")

    assert result.text == "OCR fallback"
    assert result.backend == "docling"


def test_pdf_fallback_bubbles_ocr_configuration_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_pdf_extract(content: bytes) -> list[str]:
        raise IntakeError("No readable text was found in this PDF.")

    monkeypatch.setattr(intake_extract, "extract_pdf_pages", fake_pdf_extract)
    monkeypatch.setattr(intake_extract, "docling_is_available", lambda: True)
    monkeypatch.setattr(
        intake_extract,
        "extract_docling_document",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OCRSupportMissing("OCR is not configured.")
        ),
    )

    with pytest.raises(OCRSupportMissing):
        extract_contract_document("scan.pdf", b"%PDF")


@pytest.mark.skipif(
    importlib.util.find_spec("pypdf") is None,
    reason="pypdf is not installed in this Python environment",
)
def test_pdf_without_text_is_rejected() -> None:
    with pytest.raises(IntakeError):
        extract_pdf_text(
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Count 0>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
        )
