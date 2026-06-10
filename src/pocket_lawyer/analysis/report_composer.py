from __future__ import annotations

from pocket_lawyer.domain import ClauseFinding, SUPPORTED_CONTRACT_TYPES


DISCLAIMER = (
    "This report is legal information, not legal advice. It may miss context "
    "or jurisdiction-specific issues. Consult a qualified lawyer before making "
    "important decisions."
)


def build_summary(
    risk_level: str,
    risk_score: int,
    findings: list[ClauseFinding],
    contract_type: str,
) -> str:
    red_count = sum(1 for finding in findings if finding.risk_level == "red")
    yellow_count = sum(1 for finding in findings if finding.risk_level == "yellow")
    green_count = sum(1 for finding in findings if finding.risk_level == "green")

    if not findings:
        label = SUPPORTED_CONTRACT_TYPES[contract_type].lower()
        return (
            f"No known high-risk {label} clauses were detected by the current "
            "rule set. Review the full contract carefully before signing."
        )

    label = SUPPORTED_CONTRACT_TYPES[contract_type].lower()
    return (
        f"Overall {label} risk is {risk_level} ({risk_score}/100): "
        f"{red_count} red, {yellow_count} yellow, and {green_count} green findings."
    )


def build_negotiation_script(findings: list[ClauseFinding]) -> str:
    risky_findings = [
        finding for finding in findings if finding.risk_level in {"red", "yellow"}
    ][:4]

    if not risky_findings:
        return (
            "Hi, thank you for sharing the agreement. I have reviewed the key "
            "terms and do not have major concerns from my initial review. Please "
            "confirm that all discussed compensation, role, and notice-period "
            "terms are reflected in the final agreement."
        )

    bullets = "\n".join(
        f"- {finding.title}: {finding.negotiation_tip}" for finding in risky_findings
    )
    return (
        "Hi, thank you for sharing the agreement. I reviewed the terms and would "
        "like to clarify a few points before signing:\n\n"
        f"{bullets}\n\n"
        "Could we please revise these clauses or confirm the intended limits in "
        "writing? I am happy to move forward once these points are clear."
    )
