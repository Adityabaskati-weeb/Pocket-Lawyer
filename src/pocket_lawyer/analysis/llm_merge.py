from __future__ import annotations

from dataclasses import replace

from pocket_lawyer.domain import ClauseFinding, LLMClauseAssessment


def merge_llm_annotations(
    findings: list[ClauseFinding],
    assessments: list[LLMClauseAssessment],
    *,
    min_confidence: float,
) -> list[ClauseFinding]:
    if not findings or not assessments:
        return findings

    enriched: list[ClauseFinding] = []
    for finding in findings:
        assessment = _best_matching_assessment(
            finding, assessments, min_confidence=min_confidence
        )
        if assessment is None:
            enriched.append(finding)
            continue

        enriched.append(
            replace(
                finding,
                analysis_method="rule+llm",
                llm_confidence=round(assessment.confidence, 2),
                llm_reasoning_summary=assessment.reasoning_summary,
                playbook_titles_used=assessment.playbook_titles_used,
            )
        )
    return enriched


def apply_llm_status_override(
    status: str,
    findings: list[ClauseFinding],
    assessments: list[LLMClauseAssessment],
    *,
    min_confidence: float,
) -> str:
    if not assessments:
        return status

    finding_keys = {
        (finding.source_segment_index, finding.category)
        for finding in findings
        if finding.source_segment_index is not None
    }

    for assessment in assessments:
        if assessment.confidence < min_confidence:
            continue
        if assessment.needs_lawyer_review:
            return "review"
        if assessment.assessment_status == "finding":
            key = (assessment.segment_index, assessment.category)
            if key not in finding_keys:
                return "review"
        if assessment.assessment_status == "uncertain" and status == "clear":
            status = "uncertain"

    return status


def _best_matching_assessment(
    finding: ClauseFinding,
    assessments: list[LLMClauseAssessment],
    *,
    min_confidence: float,
) -> LLMClauseAssessment | None:
    if finding.source_segment_index is None:
        return None

    candidates = [
        assessment
        for assessment in assessments
        if assessment.confidence >= min_confidence
        and assessment.assessment_status == "finding"
        and assessment.segment_index == finding.source_segment_index
        and (
            assessment.category == finding.category
            or assessment.category == "unknown"
        )
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda assessment: assessment.confidence)
