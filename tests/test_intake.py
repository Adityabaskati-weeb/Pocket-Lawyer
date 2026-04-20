from __future__ import annotations

import importlib.util

import pytest

from pocket_lawyer.intake import (
    IntakeError,
    UnsupportedFileType,
    extract_contract_text,
    extract_pdf_text,
)


def test_extracts_utf8_text_file() -> None:
    text = extract_contract_text(
        "contract.txt",
        "Both parties may terminate with 30 days notice.".encode("utf-8"),
    )

    assert text == "Both parties may terminate with 30 days notice."


def test_rejects_unsupported_file_type() -> None:
    with pytest.raises(UnsupportedFileType):
        extract_contract_text("contract.docx", b"not supported yet")


def test_rejects_empty_text_file() -> None:
    with pytest.raises(IntakeError):
        extract_contract_text("contract.txt", b"   ")


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
