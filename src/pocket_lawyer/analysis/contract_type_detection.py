from __future__ import annotations

from pocket_lawyer.domain import normalize_contract_type
from pocket_lawyer.intake.models import ExtractedDocument


CONTRACT_TYPE_SIGNALS = {
    "employment": {
        "employment agreement": 6,
        "employment contract": 6,
        "offer letter": 5,
        "employee": 3,
        "employer": 3,
        "salary": 2,
        "non-compete": 2,
    },
    "freelancer": {
        "freelancer statement of work": 7,
        "statement of work": 5,
        "freelancer": 5,
        "milestone invoice": 3,
        "unlimited revisions": 3,
        "client may request": 2,
    },
    "rent": {
        "residential rent agreement": 7,
        "rent agreement": 6,
        "lease agreement": 5,
        "landlord": 4,
        "tenant": 4,
        "security deposit": 3,
        "premises": 2,
    },
    "nda": {
        "non-disclosure agreement": 7,
        "confidentiality agreement": 6,
        "confidential": 4,
        "recipient": 3,
        "disclosing party": 3,
        "court order": 1,
    },
    "vendor": {
        "vendor agreement": 7,
        "service agreement": 6,
        "service provider": 5,
        "vendor": 4,
        "net 30": 3,
        "scope change": 2,
    },
    "loan": {
        "personal loan agreement": 7,
        "loan agreement": 6,
        "borrower": 5,
        "lender": 5,
        "emi schedule": 3,
        "blank cheque": 3,
        "interest rate": 2,
    },
}


def detect_contract_type_for_upload(
    document: ExtractedDocument,
    *,
    source_name: str,
    requested_contract_type: object,
) -> str:
    requested = (
        normalize_contract_type(requested_contract_type)
        if isinstance(requested_contract_type, str)
        else "employment"
    )
    haystack = f"{source_name}\n{document.text[:2500]}".lower().replace("_", " ")
    scores = {
        contract_type: sum(
            weight for phrase, weight in signals.items() if phrase in haystack
        )
        for contract_type, signals in CONTRACT_TYPE_SIGNALS.items()
    }
    detected, detected_score = max(scores.items(), key=lambda item: item[1])
    requested_score = scores.get(requested, 0)

    if detected_score >= 5 and detected_score >= requested_score + 2:
        return detected

    return requested
