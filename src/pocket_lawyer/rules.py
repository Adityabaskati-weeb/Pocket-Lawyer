from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pocket_lawyer.domain.contract_types import (
    CONTRACT_TYPE_ALIASES,
    SUPPORTED_CONTRACT_TYPES,
    normalize_contract_type,
)
from pocket_lawyer.knowledge import load_clause_rules as load_clause_rule_records
from pocket_lawyer.models import RiskLevel


@dataclass(frozen=True)
class ClauseRule:
    title: str
    category: str
    risk_level: RiskLevel
    risk_score: int
    patterns: tuple[str, ...]
    plain_language_summary: str
    why_it_matters: str
    suggested_replacement: str
    negotiation_tip: str
    contract_types: tuple[str, ...] = ("employment",)

@lru_cache(maxsize=1)
def load_clause_rules() -> tuple[ClauseRule, ...]:
    records = load_clause_rule_records()
    return tuple(
        ClauseRule(
            title=record["title"],
            category=record["category"],
            risk_level=record["risk_level"],
            risk_score=int(record["risk_score"]),
            patterns=tuple(record["patterns"]),
            plain_language_summary=record["plain_language_summary"],
            why_it_matters=record["why_it_matters"],
            suggested_replacement=record["suggested_replacement"],
            negotiation_tip=record["negotiation_tip"],
            contract_types=tuple(record["contract_types"]),
        )
        for record in records
    )


CLAUSE_RULES = load_clause_rules()
