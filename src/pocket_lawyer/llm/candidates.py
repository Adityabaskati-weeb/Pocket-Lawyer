from __future__ import annotations

from dataclasses import dataclass

from pocket_lawyer.domain import ClauseFinding, PlaybookMatch
from pocket_lawyer.knowledge import (
    retrieve_playbook_matches,
    retrieve_segment_playbook_matches,
)
from pocket_lawyer.segmentation import ClauseSegment


@dataclass(frozen=True)
class ClauseAnalysisCandidate:
    segment: ClauseSegment
    existing_finding: ClauseFinding | None
    playbook_matches: list[PlaybookMatch]
    priority: float


def select_clause_candidates(
    *,
    contract_type: str,
    segments: list[ClauseSegment],
    findings: list[ClauseFinding],
    limit: int,
) -> list[ClauseAnalysisCandidate]:
    if limit <= 0:
        return []

    segments_by_index = {segment.index: segment for segment in segments}
    candidates: list[ClauseAnalysisCandidate] = []
    seen_segment_indexes: set[int] = set()

    for finding in sorted(findings, key=lambda item: (-item.risk_score, item.title)):
        if finding.risk_level == "green":
            continue
        if finding.source_segment_index is None:
            continue
        segment = segments_by_index.get(finding.source_segment_index)
        if segment is None or segment.index in seen_segment_indexes:
            continue

        playbook_matches = retrieve_playbook_matches(
            contract_type=contract_type,
            document_text=segment.text,
            findings=[finding],
            limit=3,
            fallback=False,
        )
        candidates.append(
            ClauseAnalysisCandidate(
                segment=segment,
                existing_finding=finding,
                playbook_matches=playbook_matches,
                priority=100.0 + finding.risk_score,
            )
        )
        seen_segment_indexes.add(segment.index)

    for segment in segments:
        if segment.index in seen_segment_indexes:
            continue
        playbook_matches = retrieve_segment_playbook_matches(
            contract_type=contract_type,
            segment_text=segment.text,
            limit=3,
        )
        if not playbook_matches:
            continue
        candidates.append(
            ClauseAnalysisCandidate(
                segment=segment,
                existing_finding=None,
                playbook_matches=playbook_matches,
                priority=playbook_matches[0].relevance_score,
            )
        )

    candidates.sort(
        key=lambda candidate: (
            -candidate.priority,
            candidate.segment.index,
        )
    )
    return candidates[:limit]


def candidate_to_prompt_payload(candidate: ClauseAnalysisCandidate) -> dict[str, object]:
    payload = {
        "segment_index": candidate.segment.index,
        "segment_label": candidate.segment.label or "",
        "clause_text": candidate.segment.text,
        "playbook_matches": [
            {
                "title": match.title,
                "category": match.category,
                "risk_level": match.risk_level,
                "risk_score": match.risk_score,
                "plain_language_summary": match.plain_language_summary,
                "why_it_matters": match.why_it_matters,
                "suggested_replacement": match.suggested_replacement,
                "negotiation_tip": match.negotiation_tip,
            }
            for match in candidate.playbook_matches
        ],
    }
    if candidate.existing_finding is None:
        payload["existing_rule_finding"] = {}
    else:
        payload["existing_rule_finding"] = {
            "title": candidate.existing_finding.title,
            "category": candidate.existing_finding.category,
            "risk_level": candidate.existing_finding.risk_level,
            "risk_score": candidate.existing_finding.risk_score,
            "plain_language_summary": candidate.existing_finding.plain_language_summary,
            "why_it_matters": candidate.existing_finding.why_it_matters,
        }
    return payload
