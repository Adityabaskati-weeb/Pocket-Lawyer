from dataclasses import replace

from pocket_lawyer.analysis.llm_merge import apply_llm_status_override
from pocket_lawyer.analysis.rules_engine import match_rules
from pocket_lawyer.llm.service import run_llm_clause_analysis
from pocket_lawyer.models import LLMClauseAssessment
from pocket_lawyer.segmentation import segment_contract_text
from pocket_lawyer.settings import get_settings


class FakeClauseAnalysisClient:
    def analyze(self, **_: object) -> dict[str, object]:
        return {
            "assessments": [
                {
                    "segment_index": 0,
                    "assessment_status": "finding",
                    "finding_title": "Post-employment non-compete",
                    "category": "non_compete",
                    "risk_level": "red",
                    "confidence": 0.88,
                    "reasoning_summary": "The clause restricts post-employment work for two years.",
                    "evidence_text": "The employee agrees to a non-compete for 24 months.",
                    "suggested_replacement": "Use a narrow non-solicitation clause instead.",
                    "negotiation_tip": "Ask for role-specific limits and a much shorter duration.",
                    "needs_lawyer_review": True,
                    "playbook_titles_used": ["Post-employment non-compete"],
                }
            ]
        }


def test_run_llm_clause_analysis_skips_without_api_key() -> None:
    text = "The employee agrees to a non-compete for 24 months after employment."
    segments = segment_contract_text(text)
    findings = match_rules(segments, "employment")
    settings = replace(
        get_settings(),
        enable_llm=True,
        llm_provider="openai",
        llm_api_key=None,
    )

    result = run_llm_clause_analysis(
        contract_type="employment",
        segments=segments,
        findings=findings,
        settings=settings,
    )

    assert result.status == "skipped"
    assert "API key" in (result.error or "")


def test_run_llm_clause_analysis_parses_mocked_response() -> None:
    text = "The employee agrees to a non-compete for 24 months after employment."
    segments = segment_contract_text(text)
    findings = match_rules(segments, "employment")
    settings = replace(
        get_settings(),
        enable_llm=True,
        llm_api_key="test-key",
        llm_max_candidates=3,
    )

    result = run_llm_clause_analysis(
        contract_type="employment",
        segments=segments,
        findings=findings,
        settings=settings,
        client=FakeClauseAnalysisClient(),
    )

    assert result.status == "completed"
    assert result.provider == "openai"
    assert result.model == settings.llm_model
    assert len(result.assessments) == 1
    assert result.assessments[0].category == "non_compete"
    assert result.assessments[0].playbook_titles_used == [
        "Post-employment non-compete"
    ]


def test_run_llm_clause_analysis_supports_ollama_without_api_key() -> None:
    text = "The employee agrees to a non-compete for 24 months after employment."
    segments = segment_contract_text(text)
    findings = match_rules(segments, "employment")
    settings = replace(
        get_settings(),
        enable_llm=True,
        llm_provider="ollama",
        llm_model="qwen3:1.7b",
        llm_api_base="http://127.0.0.1:11434/api",
        llm_api_key=None,
        llm_max_candidates=3,
    )

    result = run_llm_clause_analysis(
        contract_type="employment",
        segments=segments,
        findings=findings,
        settings=settings,
        client=FakeClauseAnalysisClient(),
    )

    assert result.status == "completed"
    assert result.provider == "ollama"
    assert result.model == "qwen3:1.7b"
    assert result.assessments[0].category == "non_compete"


def test_apply_llm_status_override_escalates_new_high_confidence_findings() -> None:
    status = apply_llm_status_override(
        "clear",
        findings=[],
        assessments=[
            LLMClauseAssessment(
                segment_index=1,
                segment_label="2",
                assessment_status="finding",
                finding_title="Broad IP ownership",
                category="ip_ownership",
                risk_level="red",
                confidence=0.9,
                reasoning_summary="The clause captures side projects outside work.",
                evidence_text="All intellectual property created outside work hours belongs to the employer.",
                suggested_replacement="Limit ownership to work product created within job duties.",
                negotiation_tip="Ask for a carve-out for prior and side-project IP.",
                needs_lawyer_review=False,
                playbook_titles_used=["Broad IP ownership"],
            )
        ],
        min_confidence=0.7,
    )

    assert status == "review"


def test_settings_default_to_ollama_local_profile(monkeypatch) -> None:
    from pocket_lawyer import settings as settings_module

    monkeypatch.setenv("POCKET_LAWYER_LLM_PROVIDER", "ollama")
    monkeypatch.delenv("POCKET_LAWYER_LLM_MODEL", raising=False)
    monkeypatch.delenv("POCKET_LAWYER_LLM_API_BASE", raising=False)
    monkeypatch.delenv("POCKET_LAWYER_LLM_API_KEY", raising=False)
    monkeypatch.delenv("POCKET_LAWYER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings_module.get_settings.cache_clear()
    try:
        settings = settings_module.get_settings()
    finally:
        settings_module.get_settings.cache_clear()

    assert settings.llm_provider == "ollama"
    assert settings.llm_model == "qwen3:1.7b"
    assert settings.llm_api_base == "http://127.0.0.1:11434/api"
    assert settings.llm_api_key is None
    assert settings.llm_timeout_seconds == 60.0


def test_settings_keep_openai_timeout_default(monkeypatch) -> None:
    from pocket_lawyer import settings as settings_module

    monkeypatch.setenv("POCKET_LAWYER_LLM_PROVIDER", "openai")
    monkeypatch.delenv("POCKET_LAWYER_LLM_TIMEOUT_SECONDS", raising=False)
    settings_module.get_settings.cache_clear()
    try:
        settings = settings_module.get_settings()
    finally:
        settings_module.get_settings.cache_clear()

    assert settings.llm_provider == "openai"
    assert settings.llm_timeout_seconds == 20.0
