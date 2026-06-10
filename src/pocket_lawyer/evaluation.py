from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pocket_lawyer.analysis import analyze_contract


def load_golden_cases(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Golden evaluation file must contain a JSON list.")
    return [_validate_case(case) for case in payload]


def evaluate_golden_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results = [_evaluate_case(case) for case in cases]
    passed = sum(1 for result in results if result["passed"])
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "cases": results,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    report = analyze_contract(case["text"], contract_type=case["contract_type"])
    categories = {finding.category for finding in report.findings}
    failures: list[str] = []

    if report.overall_risk_level != case["expected_risk_level"]:
        failures.append(
            "expected risk "
            f"{case['expected_risk_level']}, got {report.overall_risk_level}"
        )

    if len(report.findings) < case["min_findings"]:
        failures.append(
            f"expected at least {case['min_findings']} findings, got {len(report.findings)}"
        )

    missing_categories = [
        category
        for category in case["required_categories"]
        if category not in categories
    ]
    if missing_categories:
        failures.append(f"missing categories: {', '.join(missing_categories)}")

    return {
        "id": case["id"],
        "contract_type": case["contract_type"],
        "passed": not failures,
        "failures": failures,
        "actual_risk_level": report.overall_risk_level,
        "actual_risk_score": report.overall_risk_score,
        "actual_categories": sorted(categories),
        "finding_count": len(report.findings),
    }


def _validate_case(case: object) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise ValueError("Each golden evaluation case must be an object.")

    required_fields = {
        "id": str,
        "contract_type": str,
        "text": str,
        "expected_risk_level": str,
        "required_categories": list,
        "min_findings": int,
    }
    for field, expected_type in required_fields.items():
        if not isinstance(case.get(field), expected_type):
            raise ValueError(f"Golden case must include {field!r} as {expected_type.__name__}.")

    categories = case["required_categories"]
    if not all(isinstance(category, str) for category in categories):
        raise ValueError("Golden case required_categories must contain strings.")

    return dict(case)
