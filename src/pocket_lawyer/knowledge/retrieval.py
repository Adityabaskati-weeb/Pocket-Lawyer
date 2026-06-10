from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from pocket_lawyer.analysis.scoring_profiles import get_scoring_profile
from pocket_lawyer.domain import ClauseFinding, PlaybookMatch
from pocket_lawyer.knowledge.loaders import load_clause_rules


TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "into",
        "your",
        "have",
        "will",
        "shall",
        "must",
        "than",
        "they",
        "them",
        "their",
        "there",
        "where",
        "which",
        "when",
        "what",
        "within",
        "using",
        "after",
        "before",
        "under",
        "only",
        "both",
        "either",
        "party",
        "parties",
        "agreement",
        "contract",
        "clause",
        "employee",
        "employer",
        "borrower",
        "lender",
        "landlord",
        "tenant",
        "client",
        "customer",
        "vendor",
        "recipient",
        "company",
        "owner",
        "lessee",
        "lessor",
        "should",
        "could",
        "would",
        "about",
    }
)


@dataclass(frozen=True)
class PlaybookEntry:
    title: str
    category: str
    risk_level: str
    risk_score: int
    contract_types: tuple[str, ...]
    plain_language_summary: str
    why_it_matters: str
    suggested_replacement: str
    negotiation_tip: str
    keywords: frozenset[str]


@lru_cache(maxsize=1)
def load_playbook_entries() -> tuple[PlaybookEntry, ...]:
    records = load_clause_rules()
    return tuple(
        PlaybookEntry(
            title=record["title"],
            category=record["category"],
            risk_level=record["risk_level"],
            risk_score=int(record["risk_score"]),
            contract_types=tuple(record["contract_types"]),
            plain_language_summary=record["plain_language_summary"],
            why_it_matters=record["why_it_matters"],
            suggested_replacement=record["suggested_replacement"],
            negotiation_tip=record["negotiation_tip"],
            keywords=_keywords_for_record(record),
        )
        for record in records
    )


def retrieve_playbook_matches(
    *,
    contract_type: str,
    document_text: str,
    findings: list[ClauseFinding],
    limit: int = 5,
    fallback: bool = True,
) -> list[PlaybookMatch]:
    entries = [
        entry
        for entry in load_playbook_entries()
        if contract_type in entry.contract_types or "all" in entry.contract_types
    ]
    if not entries:
        return []

    query_terms = _keywords_for_text(document_text)
    finding_categories = {finding.category for finding in findings}
    finding_titles = {finding.title for finding in findings}
    finding_terms = _keywords_for_text(
        " ".join(
            " ".join(
                [
                    finding.title,
                    finding.category.replace("_", " "),
                    finding.matched_pattern,
                    finding.original_text,
                ]
            )
            for finding in findings
        )
    )
    critical_categories = get_scoring_profile(contract_type).critical_categories

    scored: list[tuple[float, PlaybookMatch]] = []
    for entry in entries:
        score = 0.0
        reasons: list[str] = []
        has_direct_finding_match = False

        if entry.title in finding_titles:
            score += 14.0
            reasons.append("matched_title")
            has_direct_finding_match = True

        if entry.category in finding_categories:
            score += 10.0
            reasons.append("matched_category")
            has_direct_finding_match = True

        overlap = len(entry.keywords & query_terms)
        if overlap and (findings or overlap >= 2):
            score += min(overlap, 8)
            reasons.append(f"document_overlap:{overlap}")

        finding_overlap = len(entry.keywords & finding_terms)
        if finding_overlap:
            score += min(finding_overlap, 5)
            reasons.append(f"finding_overlap:{finding_overlap}")

        if entry.category in critical_categories and score > 0:
            score += 1.5
            reasons.append("critical_category")

        if contract_type in entry.contract_types and score > 0:
            score += 0.5
            reasons.append("contract_type")

        if score <= 0:
            continue
        if not has_direct_finding_match and score < 6.0:
            continue

        scored.append(
            (
                score,
                PlaybookMatch(
                    title=entry.title,
                    category=entry.category,
                    risk_level=entry.risk_level,
                    risk_score=entry.risk_score,
                    contract_types=list(entry.contract_types),
                    plain_language_summary=entry.plain_language_summary,
                    why_it_matters=entry.why_it_matters,
                    suggested_replacement=entry.suggested_replacement,
                    negotiation_tip=entry.negotiation_tip,
                    relevance_score=round(score, 2),
                    relevance_reasons=reasons,
                ),
            )
        )

    if scored:
        scored.sort(
            key=lambda item: (
                -item[0],
                -item[1].risk_score,
                item[1].title,
            )
        )
        return _dedupe_matches([match for _, match in scored], limit=limit)

    if fallback:
        return _fallback_contract_review_topics(contract_type, entries, limit=limit)
    return []


def retrieve_segment_playbook_matches(
    *, contract_type: str, segment_text: str, limit: int = 3
) -> list[PlaybookMatch]:
    return retrieve_playbook_matches(
        contract_type=contract_type,
        document_text=segment_text,
        findings=[],
        limit=limit,
        fallback=False,
    )


def _fallback_contract_review_topics(
    contract_type: str, entries: list[PlaybookEntry], *, limit: int
) -> list[PlaybookMatch]:
    critical_categories = get_scoring_profile(contract_type).critical_categories
    fallback_entries = [
        entry for entry in entries if entry.category in critical_categories
    ] or entries
    fallback_entries = sorted(
        fallback_entries, key=lambda entry: (-entry.risk_score, entry.title)
    )[:limit]

    return [
        PlaybookMatch(
            title=entry.title,
            category=entry.category,
            risk_level=entry.risk_level,
            risk_score=entry.risk_score,
            contract_types=list(entry.contract_types),
            plain_language_summary=entry.plain_language_summary,
            why_it_matters=entry.why_it_matters,
            suggested_replacement=entry.suggested_replacement,
            negotiation_tip=entry.negotiation_tip,
            relevance_score=1.0,
            relevance_reasons=["contract_type_priority"],
        )
        for entry in fallback_entries
    ]


def _dedupe_matches(
    matches: list[PlaybookMatch], *, limit: int
) -> list[PlaybookMatch]:
    deduped: list[PlaybookMatch] = []
    seen: set[tuple[str, str]] = set()
    for match in matches:
        key = (match.category, match.title)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)
        if len(deduped) >= limit:
            break
    return deduped


def _keywords_for_record(record: dict[str, object]) -> frozenset[str]:
    fields = [
        str(record["title"]),
        str(record["category"]).replace("_", " "),
        str(record["plain_language_summary"]),
        str(record["why_it_matters"]),
        str(record["suggested_replacement"]),
        str(record["negotiation_tip"]),
        " ".join(str(contract_type) for contract_type in record["contract_types"]),
        " ".join(str(pattern) for pattern in record["patterns"]),
    ]
    return _keywords_for_text(" ".join(fields))


def _keywords_for_text(text: str) -> frozenset[str]:
    tokens = [
        token
        for token in TOKEN_RE.findall(text.lower())
        if len(token) >= 3 and token not in STOPWORDS and not token.isdigit()
    ]
    return frozenset(tokens)
