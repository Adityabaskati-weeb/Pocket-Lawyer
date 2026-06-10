from __future__ import annotations

from pocket_lawyer.domain import ClauseFinding
from pocket_lawyer.segmentation import ClauseSegment


def confidence_score(
    text: str,
    segments: list[ClauseSegment],
    findings: list[ClauseFinding],
) -> int:
    score = 30
    text_length = len(text)
    segment_count = len(segments)

    if text_length >= 120:
        score += 15
    if text_length >= 500:
        score += 10
    if segment_count >= 2:
        score += 10
    if segment_count >= 5:
        score += 5
    if any(segment.label for segment in segments):
        score += 5
    if findings:
        score += 10
    if len(findings) >= 2:
        score += 5
    if text_length >= 500 and not findings:
        score -= 15
    if segment_count <= 1 and text_length > 700:
        score -= 10
    if text_length < 80:
        score -= 15

    return max(10, min(95, score))


def analysis_status(risk_level: str, confidence: int) -> str:
    if confidence < 45:
        return "uncertain"
    if risk_level in {"medium", "high"}:
        return "review"
    return "clear"
