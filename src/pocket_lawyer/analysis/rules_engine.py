from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Sequence

from pocket_lawyer.domain import ClauseFinding
from pocket_lawyer.rules import CLAUSE_RULES, ClauseRule
from pocket_lawyer.segmentation import ClauseSegment, segment_contract_text


def match_rules(
    text_or_segments: str | Sequence[ClauseSegment], contract_type: str
) -> list[ClauseFinding]:
    if isinstance(text_or_segments, str):
        segments = segment_contract_text(text_or_segments)
    else:
        segments = list(text_or_segments)

    if not segments and isinstance(text_or_segments, str) and text_or_segments.strip():
        segments = [
            ClauseSegment(
                index=0,
                text=text_or_segments.strip(),
                start_offset=0,
                end_offset=len(text_or_segments.strip()),
            )
        ]

    findings: list[ClauseFinding] = []

    for rule in rules_for_contract_type(contract_type):
        matched_segment, match = first_segment_match(segments, rule.patterns)
        if not match or matched_segment is None:
            continue

        original_text = extract_context(matched_segment.text, match.start(), match.end())
        findings.append(
            ClauseFinding(
                title=rule.title,
                category=rule.category,
                original_text=original_text,
                risk_level=rule.risk_level,
                risk_score=rule.risk_score,
                plain_language_summary=rule.plain_language_summary,
                why_it_matters=rule.why_it_matters,
                suggested_replacement=rule.suggested_replacement,
                negotiation_tip=rule.negotiation_tip,
                matched_pattern=match.group(0).strip(),
                source_segment_index=matched_segment.index,
                source_segment_label=matched_segment.label,
                source_span_start=matched_segment.start_offset + match.start(),
                source_span_end=matched_segment.start_offset + match.end(),
            )
        )

    return sorted(findings, key=lambda finding: (-finding.risk_score, finding.title))


def rules_for_contract_type(contract_type: str) -> list[ClauseRule]:
    return [
        rule
        for rule in CLAUSE_RULES
        if contract_type in rule.contract_types or "all" in rule.contract_types
    ]


def first_match(text: str, patterns: Iterable[str]) -> re.Match[str] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match
    return None


def first_segment_match(
    segments: Sequence[ClauseSegment], patterns: Iterable[str]
) -> tuple[ClauseSegment | None, re.Match[str] | None]:
    for segment in segments:
        match = first_match(segment.text, patterns)
        if match:
            return segment, match
    return None, None


def extract_context(text: str, start: int, end: int, max_chars: int = 700) -> str:
    left = max(text.rfind("\n\n", 0, start), text.rfind(". ", 0, start))
    right_candidates = [text.find("\n\n", end), text.find(". ", end)]
    right_candidates = [candidate for candidate in right_candidates if candidate != -1]
    right = min(right_candidates) + 1 if right_candidates else min(len(text), end + 320)

    if left == -1:
        left = max(0, start - 240)
    else:
        left += 1

    snippet = re.sub(r"\s+", " ", text[left:right]).strip()
    if len(snippet) <= max_chars:
        return snippet

    relative_start = max(0, start - left)
    window_start = max(0, relative_start - 220)
    return snippet[window_start : window_start + max_chars].strip()
