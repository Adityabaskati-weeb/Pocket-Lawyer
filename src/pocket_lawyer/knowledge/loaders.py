from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any


class KnowledgeValidationError(ValueError):
    """Raised when bundled legal playbook data is malformed."""


def _load_json_resource(filename: str) -> Any:
    resource = files("pocket_lawyer.knowledge.playbooks").joinpath(filename)
    return json.loads(resource.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_clause_rules() -> tuple[dict[str, Any], ...]:
    payload = _load_json_resource("clause_rules.json")
    if not isinstance(payload, list):
        raise KnowledgeValidationError("clause_rules.json must contain a list.")

    required_keys = {
        "title",
        "category",
        "risk_level",
        "risk_score",
        "patterns",
        "plain_language_summary",
        "why_it_matters",
        "suggested_replacement",
        "negotiation_tip",
        "contract_types",
    }
    validated: list[dict[str, Any]] = []
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise KnowledgeValidationError(
                f"Clause rule at index {index} must be an object."
            )
        missing = sorted(required_keys - set(entry))
        if missing:
            raise KnowledgeValidationError(
                f"Clause rule '{entry.get('title', index)}' is missing keys: {', '.join(missing)}."
            )
        if not isinstance(entry["patterns"], list) or not entry["patterns"]:
            raise KnowledgeValidationError(
                f"Clause rule '{entry['title']}' must define at least one pattern."
            )
        if not isinstance(entry["contract_types"], list) or not entry["contract_types"]:
            raise KnowledgeValidationError(
                f"Clause rule '{entry['title']}' must define at least one contract type."
            )
        validated.append(entry)
    return tuple(validated)


@lru_cache(maxsize=1)
def load_scoring_profiles() -> dict[str, dict[str, Any]]:
    payload = _load_json_resource("scoring_profiles.json")
    if not isinstance(payload, dict):
        raise KnowledgeValidationError("scoring_profiles.json must contain an object.")

    required_keys = {
        "category_weights",
        "red_weight",
        "yellow_weight",
        "green_credit",
        "high_threshold",
        "medium_threshold",
        "high_red_count",
        "medium_red_count",
        "medium_yellow_count",
        "critical_categories",
    }
    validated: dict[str, dict[str, Any]] = {}
    for contract_type, entry in payload.items():
        if not isinstance(entry, dict):
            raise KnowledgeValidationError(
                f"Scoring profile '{contract_type}' must be an object."
            )
        missing = sorted(required_keys - set(entry))
        if missing:
            raise KnowledgeValidationError(
                f"Scoring profile '{contract_type}' is missing keys: {', '.join(missing)}."
            )
        if not isinstance(entry["category_weights"], dict):
            raise KnowledgeValidationError(
                f"Scoring profile '{contract_type}' must define category_weights as an object."
            )
        if not isinstance(entry["critical_categories"], list):
            raise KnowledgeValidationError(
                f"Scoring profile '{contract_type}' must define critical_categories as a list."
            )
        validated[contract_type] = entry
    return validated
