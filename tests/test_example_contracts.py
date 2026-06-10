from __future__ import annotations

from pathlib import Path

import pytest

from pocket_lawyer.analysis.service import analyze_extracted_document
from pocket_lawyer.intake.extract import extract_contract_document


ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_CONTRACTS = [
    (
        "employment_offer.pdf",
        "employment",
        "high",
        {"ip_ownership", "non_compete", "compensation"},
    ),
    (
        "freelancer_sow.pdf",
        "freelancer",
        "medium",
        {"payment_terms", "scope_creep"},
    ),
    (
        "rent_agreement.pdf",
        "rent",
        "high",
        {"security_deposit", "lock_in", "privacy"},
    ),
    (
        "nda.pdf",
        "nda",
        "medium",
        {"career_restriction", "mutuality", "disclosure_exception"},
    ),
    (
        "loan_agreement.pdf",
        "loan",
        "high",
        {"security", "interest", "default"},
    ),
]


@pytest.mark.parametrize(
    ("filename", "contract_type", "expected_level", "expected_categories"),
    EXAMPLE_CONTRACTS,
)
def test_example_pdf_has_realistic_text_and_risky_findings(
    filename: str,
    contract_type: str,
    expected_level: str,
    expected_categories: set[str],
) -> None:
    path = ROOT / "demo_contracts" / filename
    document = extract_contract_document(path.name, path.read_bytes())
    report = analyze_extracted_document(document, contract_type=contract_type)
    categories = {finding.category for finding in report.findings}

    assert document.backend == "pypdf"
    assert report.overall_risk_level == expected_level
    assert report.overall_risk_score > 0
    assert any(finding.risk_level in {"red", "yellow"} for finding in report.findings)
    assert expected_categories <= categories

    extracted_text = document.text.lower()
    assert "demo" not in extracted_text
    assert "testing only" not in extracted_text
    assert "for demo" not in extracted_text
