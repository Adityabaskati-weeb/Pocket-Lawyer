from __future__ import annotations


SUPPORTED_CONTRACT_TYPES = {
    "employment": "Employment contract",
    "freelancer": "Freelancer/client contract",
    "rent": "Rent agreement",
    "nda": "NDA",
    "vendor": "Vendor/service agreement",
    "loan": "Loan agreement",
}

CONTRACT_TYPE_ALIASES = {
    "employment_contract": "employment",
    "job_offer": "employment",
    "offer_letter": "employment",
    "freelance": "freelancer",
    "freelancer_contract": "freelancer",
    "client_contract": "freelancer",
    "rent_agreement": "rent",
    "rental": "rent",
    "lease": "rent",
    "lease_agreement": "rent",
    "non_disclosure": "nda",
    "non_disclosure_agreement": "nda",
    "confidentiality_agreement": "nda",
    "service_agreement": "vendor",
    "vendor_agreement": "vendor",
    "msa": "vendor",
    "loan_agreement": "loan",
    "personal_loan": "loan",
}


def normalize_contract_type(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    candidate = CONTRACT_TYPE_ALIASES.get(normalized, normalized)
    if candidate in SUPPORTED_CONTRACT_TYPES:
        return candidate
    return "employment"
