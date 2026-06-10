from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from pocket_lawyer.domain import ClauseFinding
from pocket_lawyer.knowledge.loaders import load_scoring_profiles


@dataclass(frozen=True)
class ScoringProfile:
    category_weights: dict[str, float]
    red_weight: int = 10
    yellow_weight: int = 4
    green_credit: int = 3
    high_threshold: int = 70
    medium_threshold: int = 35
    high_red_count: int = 2
    medium_red_count: int = 1
    medium_yellow_count: int = 2
    critical_categories: frozenset[str] = frozenset()


@lru_cache(maxsize=1)
def _load_profiles() -> dict[str, ScoringProfile]:
    payload = load_scoring_profiles()
    return {
        contract_type: ScoringProfile(
            category_weights={
                key: float(value) for key, value in record["category_weights"].items()
            },
            red_weight=int(record["red_weight"]),
            yellow_weight=int(record["yellow_weight"]),
            green_credit=int(record["green_credit"]),
            high_threshold=int(record["high_threshold"]),
            medium_threshold=int(record["medium_threshold"]),
            high_red_count=int(record["high_red_count"]),
            medium_red_count=int(record["medium_red_count"]),
            medium_yellow_count=int(record["medium_yellow_count"]),
            critical_categories=frozenset(record["critical_categories"]),
        )
        for contract_type, record in payload.items()
    }


SCORING_PROFILES: dict[str, ScoringProfile] = _load_profiles()


DEFAULT_PROFILE = ScoringProfile(category_weights={})


def get_scoring_profile(contract_type: str) -> ScoringProfile:
    return SCORING_PROFILES.get(contract_type, DEFAULT_PROFILE)


def adjusted_finding_score(finding: ClauseFinding, contract_type: str) -> int:
    profile = get_scoring_profile(contract_type)
    weight = profile.category_weights.get(finding.category, 1.0)
    return min(100, round(finding.risk_score * weight))
