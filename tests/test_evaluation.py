from __future__ import annotations

from pathlib import Path

from pocket_lawyer.evaluation import evaluate_golden_cases, load_golden_cases


ROOT = Path(__file__).resolve().parents[1]


def test_golden_evaluation_cases_pass() -> None:
    cases = load_golden_cases(ROOT / "tests" / "fixtures" / "golden_evaluation_cases.json")

    result = evaluate_golden_cases(cases)

    assert result["total"] == 6
    assert result["passed"] == 6
    assert result["failed"] == 0
    assert all(case["passed"] for case in result["cases"])
