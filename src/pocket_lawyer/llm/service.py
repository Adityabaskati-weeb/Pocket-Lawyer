from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pocket_lawyer.domain import (
    ClauseFinding,
    LLMClauseAssessment,
    LLMStatus,
    PlaybookMatch,
)
from pocket_lawyer.knowledge import (
    load_playbook_entries,
    retrieve_playbook_matches,
    retrieve_segment_playbook_matches,
)
from pocket_lawyer.llm.ollama_client import (
    OllamaClauseAnalysisClient,
    OllamaClauseAnalysisError,
)
from pocket_lawyer.llm.openai_client import (
    OpenAIClauseAnalysisClient,
    OpenAIClauseAnalysisError,
)
from pocket_lawyer.llm.prompts import (
    SYSTEM_PROMPT,
    build_clause_assessment_schema,
    build_clause_assessment_user_message,
)
from pocket_lawyer.segmentation import ClauseSegment
from pocket_lawyer.settings import AppSettings, get_settings


class ClauseAnalysisClient(Protocol):
    def analyze(
        self,
        *,
        model: str,
        system_prompt: str,
        user_message: str,
        schema: dict[str, object],
    ) -> dict[str, object]: ...


@dataclass(frozen=True)
class ClauseAnalysisCandidate:
    segment: ClauseSegment
    existing_finding: ClauseFinding | None
    playbook_matches: list[PlaybookMatch]
    priority: float


@dataclass(frozen=True)
class LLMAnalysisResult:
    status: LLMStatus
    provider: str | None = None
    model: str | None = None
    assessments: list[LLMClauseAssessment] = field(default_factory=list)
    error: str | None = None


def run_llm_clause_analysis(
    *,
    contract_type: str,
    segments: list[ClauseSegment],
    findings: list[ClauseFinding],
    settings: AppSettings | None = None,
    client: ClauseAnalysisClient | None = None,
) -> LLMAnalysisResult:
    active_settings = settings or get_settings()

    if not active_settings.enable_llm:
        return LLMAnalysisResult(status="disabled")

    if active_settings.llm_provider not in {"openai", "ollama"}:
        return LLMAnalysisResult(
            status="skipped",
            provider=active_settings.llm_provider,
            model=active_settings.llm_model,
            error=f"Unsupported LLM provider: {active_settings.llm_provider}",
        )

    if active_settings.llm_provider == "openai" and not active_settings.llm_api_key:
        return LLMAnalysisResult(
            status="skipped",
            provider=active_settings.llm_provider,
            model=active_settings.llm_model,
            error="LLM is enabled but no API key is configured.",
        )

    candidates = select_clause_candidates(
        contract_type=contract_type,
        segments=segments,
        findings=findings,
        limit=active_settings.llm_max_candidates,
    )
    if not candidates:
        return LLMAnalysisResult(
            status="skipped",
            provider=active_settings.llm_provider,
            model=active_settings.llm_model,
            error="No clause candidates qualified for LLM review.",
        )

    api_client = client or _build_provider_client(active_settings)
    schema = build_clause_assessment_schema(_known_categories())
    user_message = build_clause_assessment_user_message(
        contract_type=contract_type,
        candidates=[
            _candidate_payload(candidate)
            for candidate in candidates
        ],
    )

    try:
        raw_payload = api_client.analyze(
            model=active_settings.llm_model,
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            schema=schema,
        )
    except (OpenAIClauseAnalysisError, OllamaClauseAnalysisError) as exc:
        return LLMAnalysisResult(
            status="error",
            provider=active_settings.llm_provider,
            model=active_settings.llm_model,
            error=str(exc),
        )

    assessments = _parse_assessments(raw_payload, candidates)
    return LLMAnalysisResult(
        status="completed",
        provider=active_settings.llm_provider,
        model=active_settings.llm_model,
        assessments=assessments,
    )


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

    for finding in sorted(
        findings, key=lambda item: (-item.risk_score, item.title)
    ):
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


def _known_categories() -> list[str]:
    return sorted({entry.category for entry in load_playbook_entries()})


def _build_provider_client(active_settings: AppSettings) -> ClauseAnalysisClient:
    if active_settings.llm_provider == "ollama":
        return OllamaClauseAnalysisClient(
            api_base=active_settings.llm_api_base,
            api_key=active_settings.llm_api_key,
            timeout_seconds=active_settings.llm_timeout_seconds,
        )

    return OpenAIClauseAnalysisClient(
        api_base=active_settings.llm_api_base,
        api_key=active_settings.llm_api_key or "",
        timeout_seconds=active_settings.llm_timeout_seconds,
    )


def _candidate_payload(candidate: ClauseAnalysisCandidate) -> dict[str, object]:
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


def _parse_assessments(
    payload: dict[str, object], candidates: list[ClauseAnalysisCandidate]
) -> list[LLMClauseAssessment]:
    raw_assessments = payload.get("assessments")
    if not isinstance(raw_assessments, list):
        return []

    candidates_by_index = {
        candidate.segment.index: candidate for candidate in candidates
    }
    assessments: list[LLMClauseAssessment] = []

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
            set(_known_categories()) | {"unknown"},
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
