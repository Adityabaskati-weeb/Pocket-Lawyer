from pocket_lawyer.analysis.scoring import overall_risk_score
from pocket_lawyer.domain import ClauseFinding


def make_finding(category: str, risk_level: str, risk_score: int) -> ClauseFinding:
    return ClauseFinding(
        title="Synthetic finding",
        category=category,
        original_text="Synthetic clause text.",
        risk_level=risk_level,
        risk_score=risk_score,
        plain_language_summary="Synthetic summary.",
        why_it_matters="Synthetic reason.",
        suggested_replacement="Synthetic replacement.",
        negotiation_tip="Synthetic tip.",
        matched_pattern="synthetic",
    )


def test_contract_type_profiles_adjust_risk_scoring() -> None:
    finding = make_finding("security", "red", 70)

    loan_score = overall_risk_score([finding], "loan")
    employment_score = overall_risk_score([finding], "employment")

    assert loan_score > employment_score
