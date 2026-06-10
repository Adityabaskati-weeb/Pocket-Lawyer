from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from pocket_lawyer.intake.extract import (
    build_text_document,
    extract_contract_document,
)
from pocket_lawyer.intake.models import ExtractedDocument


@dataclass(frozen=True)
class ContractSubmission:
    document: ExtractedDocument
    source_name: str
    source_file_bytes: bytes | None = None


def build_contract_submission(payload: dict[str, Any]) -> ContractSubmission:
    text = payload.get("text")
    if isinstance(text, str) and text.strip():
        source_name = clean_source_name(payload.get("source_name")) or "Pasted contract"
        return ContractSubmission(
            document=build_text_document(
                text,
                filename=source_name,
                backend="pasted_text",
            ),
            source_name=source_name,
        )

    filename = payload.get("filename")
    content_base64 = payload.get("content_base64")
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("Provide text or an uploaded filename.")
    if not isinstance(content_base64, str) or not content_base64.strip():
        raise ValueError("Uploaded files must include base64 content.")

    try:
        content = base64.b64decode(content_base64, validate=True)
    except ValueError as exc:
        raise ValueError("Uploaded file content must be valid base64.") from exc

    return ContractSubmission(
        document=extract_contract_document(filename, content),
        source_name=filename,
        source_file_bytes=content,
    )


def clean_source_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()
