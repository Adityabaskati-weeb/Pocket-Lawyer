from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = (
    "You assist a contract-review engine with clause-level analysis. "
    "Use only the provided clause text, existing rule findings, and grounded "
    "playbook guidance. Do not invent legal authority. If the clause is "
    "ambiguous or the evidence is weak, return assessment_status='uncertain' "
    "instead of overstating risk. Keep explanations concise and evidence-based."
)


def build_clause_assessment_schema(categories: list[str]) -> dict[str, Any]:
    category_values = sorted({category for category in categories if category})
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "assessments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "segment_index": {"type": "integer"},
                        "assessment_status": {
                            "type": "string",
                            "enum": ["finding", "uncertain", "no_issue"],
                        },
                        "finding_title": {"type": "string"},
                        "category": {
                            "type": "string",
                            "enum": category_values + ["unknown"],
                        },
                        "risk_level": {
                            "type": "string",
                            "enum": ["red", "yellow", "green", "none"],
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "reasoning_summary": {"type": "string"},
                        "evidence_text": {"type": "string"},
                        "suggested_replacement": {"type": "string"},
                        "negotiation_tip": {"type": "string"},
                        "needs_lawyer_review": {"type": "boolean"},
                        "playbook_titles_used": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "segment_index",
                        "assessment_status",
                        "finding_title",
                        "category",
                        "risk_level",
                        "confidence",
                        "reasoning_summary",
                        "evidence_text",
                        "suggested_replacement",
                        "negotiation_tip",
                        "needs_lawyer_review",
                        "playbook_titles_used",
                    ],
                },
            }
        },
        "required": ["assessments"],
    }


def build_clause_assessment_user_message(
    *, contract_type: str, candidates: list[dict[str, Any]]
) -> str:
    payload = {
        "task": "Assess each contract clause candidate independently.",
        "contract_type": contract_type,
        "instructions": [
            "Return exactly one assessment object for each candidate segment index.",
            "Use known category names when they fit; otherwise use 'unknown'.",
            "If no clear issue exists, return assessment_status='no_issue' and risk_level='none'.",
            "If there is some concern but not enough certainty, return assessment_status='uncertain'.",
            "Keep evidence_text to the most relevant excerpt from the clause.",
        ],
        "candidates": candidates,
    }
    return json.dumps(payload, indent=2, ensure_ascii=True)
