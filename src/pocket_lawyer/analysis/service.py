from __future__ import annotations

import re
from dataclasses import replace

from pocket_lawyer.analysis.confidence import analysis_status, confidence_score
from pocket_lawyer.analysis.llm_merge import (
    apply_llm_status_override,
    merge_llm_annotations,
)
from pocket_lawyer.analysis.report_composer import (
    DISCLAIMER,
    build_negotiation_script,
    build_summary,
)
from pocket_lawyer.analysis.rules_engine import match_rules
from pocket_lawyer.analysis.scoring import overall_risk_level, overall_risk_score
from pocket_lawyer.domain import ClauseFinding, ContractReport, normalize_contract_type
from pocket_lawyer.intake.extract import build_text_document
from pocket_lawyer.intake.models import ExtractedBlock, ExtractedDocument
from pocket_lawyer.knowledge import retrieve_playbook_matches
from pocket_lawyer.llm import run_llm_clause_analysis
from pocket_lawyer.segmentation import segment_contract_text
from pocket_lawyer.settings import get_settings


def analyze_contract(text: str, contract_type: str = "employment") -> ContractReport:
    document = build_text_document(text, backend="pasted_text")
    return analyze_extracted_document(document, contract_type=contract_type)


def analyze_extracted_document(
    document: ExtractedDocument, contract_type: str = "employment"
) -> ContractReport:
    settings = get_settings()
    normalized_contract_type = normalize_contract_type(contract_type)
    normalized_text = normalize_text(document.text)
    segments = segment_contract_text(normalized_text)
    findings = match_rules(segments, normalized_contract_type)
    findings = attach_source_provenance(findings, document)
    playbook_matches = retrieve_playbook_matches(
        contract_type=normalized_contract_type,
        document_text=normalized_text,
        findings=findings,
    )
    llm_result = run_llm_clause_analysis(
        contract_type=normalized_contract_type,
        segments=segments,
        findings=findings,
        settings=settings,
    )
    findings = merge_llm_annotations(
        findings,
        llm_result.assessments,
        min_confidence=settings.llm_min_confidence,
    )
    risk_score = overall_risk_score(findings, normalized_contract_type)
    risk_level = overall_risk_level(risk_score, findings, normalized_contract_type)
    confidence = confidence_score(normalized_text, segments, findings)
    status = analysis_status(risk_level, confidence)
    status = apply_llm_status_override(
        status,
        findings,
        llm_result.assessments,
        min_confidence=settings.llm_min_confidence,
    )

    return ContractReport(
        contract_type=normalized_contract_type,
        overall_risk_level=risk_level,
        overall_risk_score=risk_score,
        confidence_score=confidence,
        analysis_status=status,
        summary=build_summary(
            risk_level, risk_score, findings, normalized_contract_type
        ),
        findings=findings,
        negotiation_script=build_negotiation_script(findings),
        disclaimer=DISCLAIMER,
        source_backend=document.backend,
        source_page_count=len(document.pages),
        ocr_used=document.used_ocr,
        ocr_engine=document.ocr_engine,
        playbook_matches=playbook_matches,
        llm_status=llm_result.status,
        llm_provider=llm_result.provider,
        llm_model=llm_result.model,
        llm_error=llm_result.error,
        llm_assessments=llm_result.assessments,
    )


def normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def attach_source_provenance(
    findings: list[ClauseFinding], document: ExtractedDocument
) -> list[ClauseFinding]:
    if not document.blocks:
        return findings

    enriched: list[ClauseFinding] = []
    for finding in findings:
        block = _find_source_block(document.blocks, finding)
        if block is None:
            enriched.append(finding)
            continue

        enriched.append(
            replace(
                finding,
                source_page_number=block.page_number,
                source_block_index=block.index,
                source_block_label=block.label,
                source_bounds=block.bounds.to_dict() if block.bounds else None,
            )
        )
    return enriched


def _find_source_block(
    blocks: list[ExtractedBlock], finding: ClauseFinding
) -> ExtractedBlock | None:
    if finding.source_span_start is None or finding.source_span_end is None:
        return None

    for block in blocks:
        if (
            finding.source_span_start < block.char_end
            and finding.source_span_end > block.char_start
        ):
            return block

    return None
