from __future__ import annotations

import re
from collections.abc import Iterable

from pocket_lawyer.models import ClauseFinding, ContractReport
from pocket_lawyer.rules import (
    CLAUSE_RULES,
    SUPPORTED_CONTRACT_TYPES,
    ClauseRule,
    normalize_contract_type,
)


DISCLAIMER = (
    "This report is legal information, not legal advice. It may miss context "
    "or jurisdiction-specific issues. Consult a qualified lawyer before making "
    "important decisions."
)


def analyze_contract(text: str, contract_type: str = "employment") -> ContractReport:
    """Analyze contract text and return a deterministic risk report."""

    normalized_contract_type = normalize_contract_type(contract_type)
    normalized_text = _normalize_text(text)
    findings = _match_rules(
        normalized_text, _rules_for_contract_type(normalized_contract_type)
    )
    risk_score = _overall_risk_score(findings)
    risk_level = _overall_risk_level(risk_score, findings)

    return ContractReport(
        contract_type=normalized_contract_type,
        overall_risk_level=risk_level,
        overall_risk_score=risk_score,
        summary=_build_summary(
            risk_level, risk_score, findings, normalized_contract_type
        ),
        findings=findings,
        negotiation_script=_build_negotiation_script(findings),
        disclaimer=DISCLAIMER,
    )


def _normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _match_rules(text: str, rules: Iterable[ClauseRule]) -> list[ClauseFinding]:
    findings: list[ClauseFinding] = []

    for rule in rules:
        match = _first_match(text, rule.patterns)
        if not match:
            continue

        original_text = _extract_context(text, match.start(), match.end())
        findings.append(
            ClauseFinding(
                title=rule.title,
                category=rule.category,
                original_text=original_text,
                risk_level=rule.risk_level,
                risk_score=rule.risk_score,
                plain_language_summary=rule.plain_language_summary,
                why_it_matters=rule.why_it_matters,
                suggested_replacement=rule.suggested_replacement,
                negotiation_tip=rule.negotiation_tip,
                matched_pattern=match.group(0).strip(),
            )
        )

    return sorted(findings, key=lambda finding: (-finding.risk_score, finding.title))


def _rules_for_contract_type(contract_type: str) -> list[ClauseRule]:
    return [
        rule
        for rule in CLAUSE_RULES
        if contract_type in rule.contract_types or "all" in rule.contract_types
    ]


def _first_match(text: str, patterns: Iterable[str]) -> re.Match[str] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match
    return None


def _extract_context(text: str, start: int, end: int, max_chars: int = 700) -> str:
    left = max(text.rfind("\n\n", 0, start), text.rfind(". ", 0, start))
    right_candidates = [text.find("\n\n", end), text.find(". ", end)]
    right_candidates = [candidate for candidate in right_candidates if candidate != -1]
    right = min(right_candidates) + 1 if right_candidates else min(len(text), end + 320)

    if left == -1:
        left = max(0, start - 240)
    else:
        left += 1

    snippet = re.sub(r"\s+", " ", text[left:right]).strip()
    if len(snippet) <= max_chars:
        return snippet

    relative_start = max(0, start - left)
    window_start = max(0, relative_start - 220)
    return snippet[window_start : window_start + max_chars].strip()


def _overall_risk_score(findings: list[ClauseFinding]) -> int:
    if not findings:
        return 0

    red_count = sum(1 for finding in findings if finding.risk_level == "red")
    yellow_count = sum(1 for finding in findings if finding.risk_level == "yellow")
    green_count = sum(1 for finding in findings if finding.risk_level == "green")
    highest = max(finding.risk_score for finding in findings)

    weighted = highest + red_count * 10 + yellow_count * 4 - green_count * 3
    return max(0, min(100, weighted))


def _overall_risk_level(score: int, findings: list[ClauseFinding]) -> str:
    red_count = sum(1 for finding in findings if finding.risk_level == "red")
    yellow_count = sum(1 for finding in findings if finding.risk_level == "yellow")

    if score >= 70 or red_count >= 2:
        return "high"
    if score >= 35 or red_count == 1 or yellow_count >= 2:
        return "medium"
    return "low"


def _build_summary(
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
            "demo rule set. Review the full contract carefully before signing."
        )

    label = SUPPORTED_CONTRACT_TYPES[contract_type].lower()
    return (
        f"Overall {label} risk is {risk_level} ({risk_score}/100): "
        f"{red_count} red, {yellow_count} yellow, and {green_count} green findings."
    )


def _build_negotiation_script(findings: list[ClauseFinding]) -> str:
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
