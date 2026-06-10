from pocket_lawyer.segmentation import segment_contract_text


def test_segments_numbered_contract_blocks() -> None:
    segments = segment_contract_text(
        """
        1. The borrower shall provide a blank cheque as security.
        2. The lender may increase the interest rate at its sole discretion.

        3. The EMI schedule is attached as Annexure A.
        """
    )

    assert len(segments) == 3
    assert segments[0].label == "1."
    assert "blank cheque" in segments[0].text
    assert segments[1].label == "2."
    assert "interest rate" in segments[1].text


def test_segments_paragraph_style_contracts() -> None:
    segments = segment_contract_text(
        """
        The employee agrees to a non-compete for 24 months after employment.

        Either party may terminate this agreement by giving 30 days notice.
        """
    )

    assert len(segments) == 2
    assert segments[0].label is None
    assert "non-compete" in segments[0].text


def test_segments_inline_numbered_clauses() -> None:
    segments = segment_contract_text(
        "1. The borrower shall provide a blank cheque as security. 2. The lender may increase the interest rate at its sole discretion."
    )

    assert len(segments) == 2
    assert segments[0].label == "1."
    assert segments[1].label == "2."
