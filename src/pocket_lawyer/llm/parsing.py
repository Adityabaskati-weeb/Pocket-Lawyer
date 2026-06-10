from __future__ import annotations

from pocket_lawyer.domain import LLMClauseAssessment, PlaybookMatch
from pocket_lawyer.llm.candidates import ClauseAnalysisCandidate


def parse_clause_assessments(
    payload: dict[str, object],
    candidates: list[ClauseAnalysisCandidate],
    *,
    known_categories: list[str],
) -> list[LLMClauseAssessment]:
    raw_assessments = payload.get("assessments")
    if not isinstance(raw_assessments, list):
        return []

    candidates_by_index = {
        candidate.segment.index: candidate for candidate in candidates
    }
    assessments: list[LLMClauseAssessment] = []
    allowed_categories = set(known_categories) | {"unknown"}

    for raw_assessment in raw_assessments:
        if not isinstance(raw_assessment, dict):
            continue
        try:
            segment_index = int(raw_assessment.get("segment_index"))
        except (TypeError, ValueError):
            continue

        candidate = candidates_by_index.get(segment_index)
        if candidate is None:
            continue

        assessment_status = _normalized_choice(
            raw_assessment.get("assessment_status"),
            {"finding", "uncertain", "no_issue"},
            default="uncertain",
        )
        category = _normalized_choice(
            raw_assessment.get("category"),
            allowed_categories,
            default="unknown",
        )
        risk_level = _normalized_choice(
            raw_assessment.get("risk_level"),
            {"red", "yellow", "green", "none"},
            default="none",
        )
        confidence = _normalized_confidence(raw_assessment.get("confidence"))
        playbook_titles_used = _validated_playbook_titles(
            raw_assessment.get("playbook_titles_used"),
            candidate.playbook_matches,
        )

        assessments.append(
            LLMClauseAssessment(
                segment_index=segment_index,
                segment_label=candidate.segment.label,
                assessment_status=assessment_status,
                finding_title=_string_value(
                    raw_assessment.get("finding_title"),
                    default=_default_finding_title(category),
                ),
                category=category,
                risk_level=risk_level,
                confidence=confidence,
                reasoning_summary=_string_value(
                    raw_assessment.get("reasoning_summary")
                ),
                evidence_text=_string_value(raw_assessment.get("evidence_text")),
                suggested_replacement=_string_value(
                    raw_assessment.get("suggested_replacement")
                ),
                negotiation_tip=_string_value(raw_assessment.get("negotiation_tip")),
                needs_lawyer_review=bool(
                    raw_assessment.get("needs_lawyer_review", False)
                ),
                playbook_titles_used=playbook_titles_used,
            )
        )

    assessments.sort(key=lambda item: (item.segment_index, -item.confidence))
    return assessments


def _validated_playbook_titles(
    raw_titles: object, matches: list[PlaybookMatch]
) -> list[str]:
    allowed_titles = {match.title for match in matches}
    if not isinstance(raw_titles, list):
        return [match.title for match in matches[:2]]

    selected = [
        title.strip()
        for title in raw_titles
        if isinstance(title, str) and title.strip() in allowed_titles
    ]
    if selected:
        return selected
    return [match.title for match in matches[:2]]


def _normalized_choice(
    raw_value: object, allowed: set[str], *, default: str
) -> str:
    if not isinstance(raw_value, str):
        return default
    value = raw_value.strip().lower()
    if value in allowed:
        return value
    return default


def _normalized_confidence(raw_value: object) -> float:
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))


def _string_value(raw_value: object, *, default: str = "") -> str:
    if not isinstance(raw_value, str):
        return default
    return raw_value.strip()


def _default_finding_title(category: str) -> str:
    if category == "unknown":
        return "Clause requires review"
    return category.replace("_", " ").title()
