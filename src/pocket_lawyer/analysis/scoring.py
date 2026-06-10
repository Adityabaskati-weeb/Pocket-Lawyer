from __future__ import annotations

from pocket_lawyer.domain import ClauseFinding
from pocket_lawyer.analysis.scoring_profiles import (
    adjusted_finding_score,
    get_scoring_profile,
)


def overall_risk_score(findings: list[ClauseFinding], contract_type: str) -> int:
    if not findings:
        return 0

    profile = get_scoring_profile(contract_type)
    red_count = sum(1 for finding in findings if finding.risk_level == "red")
    yellow_count = sum(1 for finding in findings if finding.risk_level == "yellow")
    green_count = sum(1 for finding in findings if finding.risk_level == "green")
    highest = max(adjusted_finding_score(finding, contract_type) for finding in findings)

    weighted = (
        highest
        + red_count * profile.red_weight
        + yellow_count * profile.yellow_weight
        - green_count * profile.green_credit
    )
    return max(0, min(100, weighted))


def overall_risk_level(
    score: int, findings: list[ClauseFinding], contract_type: str
) -> str:
    profile = get_scoring_profile(contract_type)
    red_count = sum(1 for finding in findings if finding.risk_level == "red")
    yellow_count = sum(1 for finding in findings if finding.risk_level == "yellow")
    has_critical_red = any(
        finding.risk_level == "red" and finding.category in profile.critical_categories
        for finding in findings
    )

    if score >= profile.high_threshold or red_count >= profile.high_red_count or has_critical_red:
        return "high"
    if (
        score >= profile.medium_threshold
        or red_count >= profile.medium_red_count
        or yellow_count >= profile.medium_yellow_count
    ):
        return "medium"
    return "low"
