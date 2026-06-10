from __future__ import annotations

from pathlib import Path

import pytest

from pocket_lawyer.analysis.service import analyze_extracted_document
from pocket_lawyer.intake.extract import extract_contract_document


ROOT = Path(__file__).resolve().parents[1]

EXAMPLE_CONTRACTS = [
    (
        "employment_offer_demo.pdf",
        "employment",
        {"ip_ownership", "non_compete", "compensation"},
    ),
    (
        "freelancer_sow_demo.pdf",
        "freelancer",
        {"ip_payment", "payment_terms", "scope_creep"},
    ),
    (
        "rent_agreement_demo.pdf",
        "rent",
        {"security_deposit", "lock_in", "privacy"},
    ),
    (
        "nda_demo.pdf",
        "nda",
        {"confidentiality", "career_restriction", "mutuality"},
    ),
    (
        "loan_agreement_demo.pdf",
        "loan",
        {"security", "interest", "default"},
    ),
]


@pytest.mark.parametrize(
    ("filename", "contract_type", "expected_categories"), EXAMPLE_CONTRACTS
)
def test_example_pdf_has_realistic_text_and_risky_findings(
    filename: str, contract_type: str, expected_categories: set[str]
) -> None:
    path = ROOT / "demo_contracts" / filename
    document = extract_contract_document(path.name, path.read_bytes())
    report = analyze_extracted_document(document, contract_type=contract_type)
    categories = {finding.category for finding in report.findings}

    assert document.backend == "pypdf"
    assert report.overall_risk_level == "high"
    assert any(finding.risk_level in {"red", "yellow"} for finding in report.findings)
    assert expected_categories <= categories

    extracted_text = document.text.lower()
    assert "demo" not in extracted_text
    assert "testing only" not in extracted_text
    assert "for demo" not in extracted_text
