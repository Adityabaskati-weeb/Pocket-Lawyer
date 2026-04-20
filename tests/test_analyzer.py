from pocket_lawyer import analyze_contract


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
