from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pocket_lawyer.domain import ClauseFinding, LLMClauseAssessment, LLMStatus
from pocket_lawyer.knowledge import load_playbook_entries
from pocket_lawyer.llm.candidates import (
    ClauseAnalysisCandidate,
    candidate_to_prompt_payload,
    select_clause_candidates,
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
from pocket_lawyer.llm.parsing import parse_clause_assessments
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
            candidate_to_prompt_payload(candidate)
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

    assessments = parse_clause_assessments(
        raw_payload,
        candidates,
        known_categories=_known_categories(),
    )
    return LLMAnalysisResult(
        status="completed",
        provider=active_settings.llm_provider,
        model=active_settings.llm_model,
        assessments=assessments,
    )


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

