from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


RiskLevel = Literal["red", "yellow", "green"]
OverallRiskLevel = Literal["low", "medium", "high"]


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

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["findings"] = [finding.to_dict() for finding in self.findings]
        return payload
