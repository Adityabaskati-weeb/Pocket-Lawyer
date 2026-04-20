from __future__ import annotations

import pytest

from pocket_lawyer import analyze_contract
from pocket_lawyer.rules import SUPPORTED_CONTRACT_TYPES, normalize_contract_type


@pytest.mark.parametrize(
    ("contract_type", "text", "expected_category", "expected_title"),
    [
        (
            "freelancer",
            "The freelancer assigns all rights and intellectual property to the client immediately before payment.",
            "ip_payment",
            "Client owns work before payment",
        ),
        (
            "rent",
            "The landlord may retain the security deposit at sole discretion for any reason.",
            "security_deposit",
            "Deposit can be forfeited for any reason",
        ),
        (
            "nda",
            "All information shared by the company is confidential forever with no exceptions.",
            "confidentiality",
            "Perpetual confidentiality with no exclusions",
        ),
        (
            "vendor",
            "The vendor has unlimited liability for all losses including indirect and consequential losses.",
            "liability",
            "Unlimited vendor liability",
        ),
        (
            "loan",
            "The borrower shall provide a blank cheque as security.",
            "security",
            "Blank cheque or security cheque risk",
        ),
    ],
)
def test_new_contract_types_flag_red_risks(
    contract_type: str,
    text: str,
    expected_category: str,
    expected_title: str,
) -> None:
    report = analyze_contract(text, contract_type=contract_type)

    assert report.contract_type == contract_type
    assert report.overall_risk_level == "high"
    assert report.findings[0].category == expected_category
    assert report.findings[0].title == expected_title
    assert report.findings[0].risk_level == "red"


@pytest.mark.parametrize(
    ("contract_type", "text", "expected_title"),
    [
        (
            "freelancer",
            "Payment is due within 15 days of each approved milestone invoice.",
            "Milestone payment within 15 days",
        ),
        (
            "rent",
            "This 11-month rent agreement starts on 1 May.",
            "11-month rent term",
        ),
        (
            "nda",
            "Disclosure required by law or court order is permitted.",
            "Standard compelled disclosure carve-out",
        ),
        (
            "vendor",
            "Invoices are paid within 30 days after receipt.",
            "Net 30 invoice payment",
        ),
        (
            "loan",
            "The EMI schedule is attached and lists monthly instalments of principal and interest.",
            "Clear EMI schedule",
        ),
    ],
)
def test_new_contract_types_have_green_baseline_rules(
    contract_type: str, text: str, expected_title: str
) -> None:
    report = analyze_contract(text, contract_type=contract_type)

    assert report.overall_risk_level == "low"
    assert report.findings[0].title == expected_title
    assert report.findings[0].risk_level == "green"


def test_contract_type_aliases_are_normalized() -> None:
    assert normalize_contract_type("rent agreement") == "rent"
    assert normalize_contract_type("service-agreement") == "vendor"
    assert normalize_contract_type("personal loan") == "loan"
    assert normalize_contract_type("unknown") == "employment"


def test_six_contract_types_are_supported() -> None:
    assert set(SUPPORTED_CONTRACT_TYPES) == {
        "employment",
        "freelancer",
        "rent",
        "nda",
        "vendor",
        "loan",
    }
