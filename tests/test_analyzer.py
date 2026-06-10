from pocket_lawyer import analyze_contract, analyze_extracted_document
from pocket_lawyer.intake import build_text_document
from pocket_lawyer.llm import LLMAnalysisResult
from pocket_lawyer.models import LLMClauseAssessment


def test_flags_broad_ip_and_non_compete_as_high_risk() -> None:
    report = analyze_contract(
        """
        All intellectual property created during employment, including outside
        work hours and side projects, belongs to the employer.

        The employee agrees to a non-compete for 24 months after employment and
        cannot work in the same technology sector.
        """
    )

    titles = {finding.title for finding in report.findings}

    assert report.overall_risk_level == "high"
    assert "Broad IP ownership" in titles
    assert "Post-employment non-compete" in titles
    assert all(finding.risk_level == "red" for finding in report.findings)
    assert "legal information, not legal advice" in report.disclaimer


def test_flags_salary_reduction_and_bond() -> None:
    report = analyze_contract(
        """
        The company may revise or reduce salary with seven days notice.
        The employee must sign a service agreement bond and repay INR 200000
        as liquidated damages if leaving within 18 months.
        """
    )

    categories = {finding.category for finding in report.findings}

    assert report.overall_risk_level == "high"
    assert "compensation" in categories
    assert "bond" in categories


def test_detects_yellow_confidentiality_and_termination_risks() -> None:
    report = analyze_contract(
        """
        The employer may terminate employment without assigning any reason.
        Confidentiality obligations survive indefinitely after the end of employment.
        """
    )

    assert report.overall_risk_level == "medium"
    assert [finding.risk_level for finding in report.findings] == ["yellow", "yellow"]


def test_detects_green_standard_notice_clause() -> None:
    report = analyze_contract(
        "Either party may terminate this agreement by giving 30 days notice."
    )

    assert report.overall_risk_level == "low"
    assert len(report.findings) == 1
    assert report.findings[0].title == "Mutual 30-day notice period"
    assert report.findings[0].risk_level == "green"


def test_no_known_findings_stays_low_risk_with_disclaimer() -> None:
    report = analyze_contract(
        "The employee will report to the product manager and work from Bengaluru."
    )

    assert report.overall_risk_level == "low"
    assert report.overall_risk_score == 0
    assert report.findings == []
    assert "No known high-risk employment contract clauses" in report.summary
    assert "not legal advice" in report.disclaimer


def test_report_serializes_to_dict() -> None:
    report = analyze_contract(
        "Both parties agree to 30 days notice and return company laptop on termination."
    )
    payload = report.to_dict()

    assert payload["contract_type"] == "employment"
    assert isinstance(payload["findings"], list)
    assert payload["findings"][0]["risk_level"] == "green"
    assert isinstance(payload["playbook_matches"], list)
    assert payload["llm_status"] == "disabled"
    assert payload["llm_assessments"] == []


def test_report_includes_confidence_and_status() -> None:
    report = analyze_contract(
        """
        1. All intellectual property created outside work hours belongs to the employer.

        2. The employee agrees to a non-compete for 24 months after employment.
        """
    )

    payload = report.to_dict()

    assert report.confidence_score >= 45
    assert report.analysis_status == "review"
    assert payload["confidence_score"] == report.confidence_score
    assert payload["analysis_status"] == "review"
    assert payload["source_backend"] == "pasted_text"
    assert payload["source_page_count"] == 1


def test_short_unmatched_text_is_marked_uncertain() -> None:
    report = analyze_contract("Work location Bengaluru.")

    assert report.overall_risk_level == "low"
    assert report.analysis_status == "uncertain"
    assert report.confidence_score < 45


def test_analyze_extracted_document_maps_findings_to_source_blocks() -> None:
    document = build_text_document(
        """
        1. All intellectual property created outside work hours belongs to the employer.

        2. The employee agrees to a non-compete for 24 months after employment.
        """,
        backend="docling",
    )

    report = analyze_extracted_document(document)

    assert report.source_backend == "docling"
    assert report.source_page_count == 1
    assert report.findings[0].source_page_number == 1
    assert report.findings[0].source_block_index == 0
    assert report.playbook_matches
    assert report.playbook_matches[0].category in {"ip_ownership", "non_compete"}


def test_no_match_report_still_includes_contract_review_topics() -> None:
    report = analyze_contract("Work location Bengaluru.")

    assert report.playbook_matches
    assert "contract_type_priority" in report.playbook_matches[0].relevance_reasons


def test_report_defaults_to_llm_disabled() -> None:
    report = analyze_contract(
        "The employer may terminate employment without assigning any reason."
    )

    assert report.llm_status == "disabled"
    assert report.llm_provider is None
    assert report.llm_model is None
    assert report.llm_assessments == []


def test_llm_annotations_are_merged_without_changing_score(monkeypatch) -> None:
    from pocket_lawyer.analysis import service as service_module

    contract_text = "The employee agrees to a non-compete for 24 months after employment."
    baseline_report = analyze_contract(contract_text)

    def fake_run_llm_clause_analysis(**_: object) -> LLMAnalysisResult:
        return LLMAnalysisResult(
            status="completed",
            provider="openai",
            model="gpt-4o-mini",
            assessments=[
                LLMClauseAssessment(
                    segment_index=0,
                    segment_label=None,
                    assessment_status="finding",
                    finding_title="Post-employment non-compete",
                    category="non_compete",
                    risk_level="red",
                    confidence=0.91,
                    reasoning_summary="The clause restricts post-employment work for two years.",
                    evidence_text="The employee agrees to a non-compete for 24 months.",
                    suggested_replacement="Replace with a narrower non-solicit clause.",
                    negotiation_tip="Ask for a short, role-specific non-solicitation clause instead.",
                    needs_lawyer_review=True,
                    playbook_titles_used=["Post-employment non-compete"],
                )
            ],
        )

    monkeypatch.setattr(
        service_module, "run_llm_clause_analysis", fake_run_llm_clause_analysis
    )

    report = analyze_contract(contract_text)

    assert report.overall_risk_score == baseline_report.overall_risk_score
    assert report.llm_status == "completed"
    assert report.llm_assessments[0].category == "non_compete"
    assert report.findings[0].analysis_method == "rule+llm"
    assert report.findings[0].llm_confidence == 0.91
    assert report.findings[0].playbook_titles_used == ["Post-employment non-compete"]
