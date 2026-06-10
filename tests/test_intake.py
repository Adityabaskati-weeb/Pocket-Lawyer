from __future__ import annotations

import base64
import importlib.util

import pytest

import pocket_lawyer.intake.extract as intake_extract
from pocket_lawyer.intake.docling_export import document_from_docling_export
from pocket_lawyer.intake import (
    DoclingArtifactsMissing,
    DoclingSupportMissing,
    IntakeError,
    OCRSupportMissing,
    UnsupportedFileType,
    build_contract_submission,
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


def test_builds_submission_from_pasted_text() -> None:
    submission = build_contract_submission(
        {
            "text": "The contractor may terminate with 30 days notice.",
            "source_name": "  Consulting Agreement  ",
        }
    )

    assert submission.document.text == "The contractor may terminate with 30 days notice."
    assert submission.document.backend == "pasted_text"
    assert submission.source_name == "Consulting Agreement"
    assert submission.source_file_bytes is None


def test_builds_submission_from_uploaded_text_file() -> None:
    content = b"The employee agrees to a 24 month non-compete."

    submission = build_contract_submission(
        {
            "filename": "employment.txt",
            "content_base64": base64.b64encode(content).decode("ascii"),
        }
    )

    assert submission.document.text == "The employee agrees to a 24 month non-compete."
    assert submission.document.backend == "utf8_text"
    assert submission.source_name == "employment.txt"
    assert submission.source_file_bytes == content


def test_rejects_invalid_uploaded_base64() -> None:
    with pytest.raises(ValueError, match="valid base64"):
        build_contract_submission(
            {
                "filename": "employment.txt",
                "content_base64": "not valid base64",
            }
        )


def test_maps_docling_export_to_extracted_document() -> None:
    document = document_from_docling_export(
        filename="contract.pdf",
        backend="docling",
        payload={
            "schema_name": "DoclingDocument",
            "version": "1.0",
            "pages": {
                "1": {
                    "size": {"width": 612, "height": 792},
                    "custom": "kept",
                }
            },
            "texts": [
                {
                    "text": "Payment is due within 30 days.",
                    "label": "paragraph",
                    "self_ref": "#/texts/0",
                    "content_layer": "body",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {"l": 10, "t": 20, "r": 200, "b": 40},
                        }
                    ],
                }
            ],
        },
        used_ocr=True,
        ocr_engine="tesseract_cli",
    )

    assert document.text == "Payment is due within 30 days."
    assert document.backend == "docling"
    assert document.used_ocr is True
    assert document.ocr_engine == "tesseract_cli"
    assert document.metadata["docling_schema"] == "DoclingDocument"
    assert document.pages[0].width == 612.0
    assert document.pages[0].height == 792.0
    assert document.pages[0].metadata == {"custom": "kept"}
    assert document.blocks[0].page_number == 1
    assert document.blocks[0].bounds is not None
    assert document.blocks[0].bounds.left == 10.0


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
