from __future__ import annotations

import re
from dataclasses import dataclass


BLOCK_BREAK_RE = re.compile(r"\n\s*\n+")
NUMBERED_PREFIX_RE = re.compile(
    r"^(?P<label>(?:clause|section)\s+\d+(?:\.\d+)*|\d+(?:\.\d+)*[\).]?|\([a-zA-Z]\)|[a-zA-Z][\).])\s+",
    flags=re.IGNORECASE,
)
INLINE_NUMBERED_PREFIX_RE = re.compile(
    r"(?P<label>(?:clause|section)\s+\d+(?:\.\d+)*|(?:\d+(?:\.\d+)+|\d+[\).])|\([a-zA-Z]\))\s+",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ClauseSegment:
    index: int
    text: str
    start_offset: int
    end_offset: int
    label: str | None = None


def segment_contract_text(text: str) -> list[ClauseSegment]:
    normalized = text.strip()
    if not normalized:
        return []

    blocks = list(BLOCK_BREAK_RE.finditer(normalized))
    segments: list[ClauseSegment] = []
    start = 0

    for block in blocks:
        segments.extend(_segments_from_block(normalized, start, block.start()))
        start = block.end()

    segments.extend(_segments_from_block(normalized, start, len(normalized)))

    if not segments:
        return [ClauseSegment(index=0, text=normalized, start_offset=0, end_offset=len(normalized))]

    return [ClauseSegment(index=i, text=s.text, start_offset=s.start_offset, end_offset=s.end_offset, label=s.label) for i, s in enumerate(segments)]


def _segments_from_block(text: str, start: int, end: int) -> list[ClauseSegment]:
    block_text = text[start:end].strip()
    if not block_text:
        return []

    raw_block = text[start:end]
    inline_segments = _split_inline_numbered_clauses(raw_block, start)
    if len(inline_segments) >= 2:
        return inline_segments

    lines = [line.strip() for line in raw_block.splitlines() if line.strip()]

    if len(lines) > 1 and sum(_looks_like_clause_start(line) for line in lines) >= max(2, len(lines) // 2 + 1):
        return _split_numbered_lines(raw_block, start)

    label = _extract_label(block_text)
    return [ClauseSegment(index=0, text=block_text, start_offset=start + raw_block.find(block_text), end_offset=start + raw_block.find(block_text) + len(block_text), label=label)]


def _split_numbered_lines(raw_block: str, block_start: int) -> list[ClauseSegment]:
    segments: list[ClauseSegment] = []
    cursor = 0
    for line in raw_block.splitlines():
        stripped = line.strip()
        line_start = raw_block.find(line, cursor)
        cursor = line_start + len(line)
        if not stripped:
            continue
        absolute_start = block_start + line_start + line.find(stripped)
        absolute_end = absolute_start + len(stripped)
        segments.append(
            ClauseSegment(
                index=0,
                text=stripped,
                start_offset=absolute_start,
                end_offset=absolute_end,
                label=_extract_label(stripped),
            )
        )
    return segments


def _split_inline_numbered_clauses(raw_block: str, block_start: int) -> list[ClauseSegment]:
    matches = [match for match in INLINE_NUMBERED_PREFIX_RE.finditer(raw_block)]
    if len(matches) < 2:
        return []

    if matches[0].start() != len(raw_block) - len(raw_block.lstrip()):
        return []

    segments: list[ClauseSegment] = []
    for index, match in enumerate(matches):
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(raw_block)
        clause_text = raw_block[match.start() : next_start].strip()
        if not clause_text:
            continue
        absolute_start = block_start + match.start()
        absolute_end = absolute_start + len(clause_text)
        segments.append(
            ClauseSegment(
                index=0,
                text=clause_text,
                start_offset=absolute_start,
                end_offset=absolute_end,
                label=match.group("label").strip(),
            )
        )
    return segments


def _looks_like_clause_start(text: str) -> bool:
    return NUMBERED_PREFIX_RE.search(text) is not None


def _extract_label(text: str) -> str | None:
    match = NUMBERED_PREFIX_RE.search(text)
    if not match:
        return None
    return match.group("label").strip()
