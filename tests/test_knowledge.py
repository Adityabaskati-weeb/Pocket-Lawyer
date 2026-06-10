from pocket_lawyer.knowledge import (
    load_clause_rules,
    load_playbook_entries,
    load_scoring_profiles,
    retrieve_playbook_matches,
)
from pocket_lawyer.domain import ClauseFinding


def test_clause_rules_bundle_is_non_empty() -> None:
    rules = load_clause_rules()

    assert len(rules) >= 20
    assert any(rule["category"] == "non_compete" for rule in rules)


def test_scoring_profiles_bundle_has_supported_profiles() -> None:
    profiles = load_scoring_profiles()

    assert set(profiles) == {
        "employment",
        "freelancer",
        "rent",
        "nda",
        "vendor",
        "loan",
    }
    assert profiles["loan"]["category_weights"]["security"] > 1.0
    assert profiles["nda"]["category_weights"]["career_restriction"] > 1.0
    assert profiles["vendor"]["category_weights"]["scope"] > 1.0


def test_playbook_entries_bundle_is_non_empty() -> None:
    entries = load_playbook_entries()

    assert len(entries) >= 20
    assert any(entry.category == "non_compete" for entry in entries)


def test_retrieve_playbook_matches_uses_findings_and_document_terms() -> None:
    finding = ClauseFinding(
        title="Post-employment non-compete",
        category="non_compete",
        original_text="The employee agrees to a non-compete for 24 months after employment.",
        risk_level="red",
        risk_score=84,
        plain_language_summary="summary",
        why_it_matters="reason",
        suggested_replacement="replacement",
        negotiation_tip="tip",
        matched_pattern="non-compete for 24 months",
    )

    matches = retrieve_playbook_matches(
        contract_type="employment",
        document_text=finding.original_text,
        findings=[finding],
        limit=3,
    )

    assert matches
    assert matches[0].category == "non_compete"
    assert "matched_category" in matches[0].relevance_reasons


def test_retrieve_playbook_matches_falls_back_to_contract_type_priorities() -> None:
    matches = retrieve_playbook_matches(
        contract_type="loan",
        document_text="The borrower and lender met in Mumbai.",
        findings=[],
        limit=3,
    )

    assert matches
    assert all("contract_type_priority" in match.relevance_reasons for match in matches)
