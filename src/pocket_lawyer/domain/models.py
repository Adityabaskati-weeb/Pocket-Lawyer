from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


RiskLevel = Literal["red", "yellow", "green"]
AssessmentRiskLevel = Literal["red", "yellow", "green", "none"]
OverallRiskLevel = Literal["low", "medium", "high"]
AnalysisStatus = Literal["clear", "review", "uncertain"]
AnalysisMethod = Literal["rule", "rule+llm"]
LLMStatus = Literal["disabled", "skipped", "completed", "error"]
LLMAssessmentStatus = Literal["finding", "uncertain", "no_issue"]


@dataclass(frozen=True)
class ClauseFinding:
    title: str
    category: str
    original_text: str
    risk_level: RiskLevel
    risk_score: int
    plain_language_summary: str
    why_it_matters: str
    suggested_replacement: str
    negotiation_tip: str
    matched_pattern: str
    source_segment_index: int | None = None
    source_segment_label: str | None = None
    source_span_start: int | None = None
    source_span_end: int | None = None
    source_page_number: int | None = None
    source_block_index: int | None = None
    source_block_label: str | None = None
    source_bounds: dict[str, float | str] | None = None
    analysis_method: AnalysisMethod = "rule"
    llm_confidence: float | None = None
    llm_reasoning_summary: str | None = None
    playbook_titles_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PlaybookMatch:
    title: str
    category: str
    risk_level: RiskLevel
    risk_score: int
    contract_types: list[str]
    plain_language_summary: str
    why_it_matters: str
    suggested_replacement: str
    negotiation_tip: str
    relevance_score: float
    relevance_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LLMClauseAssessment:
    segment_index: int
    segment_label: str | None
    assessment_status: LLMAssessmentStatus
    finding_title: str
    category: str
    risk_level: AssessmentRiskLevel
    confidence: float
    reasoning_summary: str
    evidence_text: str
    suggested_replacement: str
    negotiation_tip: str
    needs_lawyer_review: bool
    playbook_titles_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ContractReport:
    contract_type: str
    overall_risk_level: OverallRiskLevel
    overall_risk_score: int
    summary: str
    findings: list[ClauseFinding]
    negotiation_script: str
    disclaimer: str
    confidence_score: int = 0
    analysis_status: AnalysisStatus = "uncertain"
    source_backend: str | None = None
    source_page_count: int = 0
    ocr_used: bool = False
    ocr_engine: str | None = None
    playbook_matches: list[PlaybookMatch] = field(default_factory=list)
    llm_status: LLMStatus = "disabled"
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_error: str | None = None
    llm_assessments: list[LLMClauseAssessment] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        payload["playbook_matches"] = [
            match.to_dict() for match in self.playbook_matches
        ]
        payload["llm_assessments"] = [
            assessment.to_dict() for assessment in self.llm_assessments
        ]
        return payload
