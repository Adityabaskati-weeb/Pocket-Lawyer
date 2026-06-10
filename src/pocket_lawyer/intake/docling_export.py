from __future__ import annotations

from typing import Any

from pocket_lawyer.intake.errors import IntakeError
from pocket_lawyer.intake.models import (
    ExtractedBlock,
    ExtractedDocument,
    ExtractedPage,
    SourceBounds,
)


def document_from_docling_export(
    *,
    filename: str,
    backend: str,
    payload: dict[str, Any],
    used_ocr: bool,
    ocr_engine: str | None,
) -> ExtractedDocument:
    text_items = payload.get("texts") or []
    page_payload = payload.get("pages") or {}
    page_meta: dict[int, dict[str, object]] = {}
    for key, value in page_payload.items():
        try:
            page_number = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            page_meta[page_number] = value

    raw_blocks: list[dict[str, object]] = []
    for item in text_items:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue

        prov_entries = item.get("prov")
        prov = prov_entries[0] if isinstance(prov_entries, list) and prov_entries else {}
        page_number = _coerce_int(
            _read_mapping_value(prov, "page_no", "page_num", "page", "pageNumber")
        )
        raw_blocks.append(
            {
                "text": text,
                "label": item.get("label"),
                "page_number": page_number,
                "bounds": _extract_bounds(prov),
                "metadata": {
                    "self_ref": item.get("self_ref"),
                    "content_layer": item.get("content_layer"),
                },
            }
        )

    if not raw_blocks:
        raise IntakeError("The uploaded file does not contain readable text.")

    blocks: list[ExtractedBlock] = []
    pages: list[ExtractedPage] = []
    text_parts: list[str] = []
    cursor = 0

    grouped_page_blocks: dict[int, list[int]] = {}

    for index, raw_block in enumerate(raw_blocks):
        block_text = str(raw_block["text"]).strip()
        if not block_text:
            continue

        if text_parts:
            text_parts.append("\n\n")
            cursor += 2

        start = cursor
        text_parts.append(block_text)
        cursor += len(block_text)
        end = cursor

        page_number = _coerce_int(raw_block.get("page_number"))
        raw_bounds = raw_block.get("bounds")
        block = ExtractedBlock(
            index=index,
            text=block_text,
            char_start=start,
            char_end=end,
            page_number=page_number,
            label=_coerce_text(raw_block.get("label")),
            bounds=raw_bounds if isinstance(raw_bounds, SourceBounds) else None,
            metadata=dict(raw_block.get("metadata") or {}),
        )
        blocks.append(block)
        if page_number is not None:
            grouped_page_blocks.setdefault(page_number, []).append(block.index)

    if grouped_page_blocks:
        for page_number in sorted(grouped_page_blocks):
            page_blocks = [blocks[index] for index in grouped_page_blocks[page_number]]
            meta = page_meta.get(page_number, {})
            pages.append(
                ExtractedPage(
                    number=page_number,
                    text="\n\n".join(block.text for block in page_blocks),
                    char_start=min(block.char_start for block in page_blocks),
                    char_end=max(block.char_end for block in page_blocks),
                    block_indexes=[block.index for block in page_blocks],
                    width=_extract_page_size(meta, "width"),
                    height=_extract_page_size(meta, "height"),
                    metadata={key: value for key, value in meta.items() if key != "size"},
                )
            )
    else:
        document_text = "".join(text_parts)
        pages.append(
            ExtractedPage(
                number=1,
                text=document_text,
                char_start=0,
                char_end=len(document_text),
                block_indexes=[block.index for block in blocks],
            )
        )

    return ExtractedDocument(
        filename=filename,
        text="".join(text_parts).strip(),
        backend=backend,
        pages=pages,
        blocks=blocks,
        used_ocr=used_ocr,
        ocr_engine=ocr_engine,
        metadata={
            "docling_schema": payload.get("schema_name"),
            "docling_version": payload.get("version"),
        },
    )


def _extract_page_size(page_meta: dict[str, object], axis: str) -> float | None:
    size = page_meta.get("size")
    if isinstance(size, dict):
        return _coerce_float(size.get(axis))
    return _coerce_float(page_meta.get(axis))


def _extract_bounds(value: object) -> SourceBounds | None:
    if not isinstance(value, dict):
        return None

    bbox = value.get("bbox") or value.get("rect")
    if not isinstance(bbox, dict):
        return None

    left = _coerce_float(
        _read_mapping_value(bbox, "l", "left", "x0", "xmin", "x_min")
    )
    top = _coerce_float(
        _read_mapping_value(bbox, "t", "top", "y0", "ymin", "y_min")
    )
    right = _coerce_float(
        _read_mapping_value(bbox, "r", "right", "x1", "xmax", "x_max")
    )
    bottom = _coerce_float(
        _read_mapping_value(bbox, "b", "bottom", "y1", "ymax", "y_max")
    )
    if None in {left, top, right, bottom}:
        return None

    return SourceBounds(left=left, top=top, right=right, bottom=bottom)


def _read_mapping_value(mapping: object, *keys: str) -> object:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
