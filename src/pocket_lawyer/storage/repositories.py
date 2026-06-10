from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pocket_lawyer.domain import ClauseFinding, ContractReport
from pocket_lawyer.intake.models import ExtractedDocument
from pocket_lawyer.settings import AppSettings, get_settings
from pocket_lawyer.storage.artifacts import LocalArtifactStore
from pocket_lawyer.storage.records import (
    JsonReportRepository,
    RecordRepository,
    SQLiteReportRepository,
    resolve_store_backend,
)
from pocket_lawyer.storage.review_requests import build_review_request_repository


DEFAULT_STORE_PATH = get_settings().store_path
DEFAULT_UPLOADS_ROOT = get_settings().uploads_path


class ReportStore:
    def __init__(
        self,
        path: str | Path | None = DEFAULT_STORE_PATH,
        *,
        uploads_root: str | Path | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        active_settings = settings or get_settings()
        self.path = Path(path) if path is not None else active_settings.store_path
        self.uploads_root = (
            Path(uploads_root)
            if uploads_root is not None
            else active_settings.uploads_path
        )
        self._records = _build_record_repository(
            active_settings.store_backend,
            self.path,
        )
        self._review_requests = build_review_request_repository(
            active_settings.store_backend,
            self.path,
        )
        self._artifacts = LocalArtifactStore(self.uploads_root)

    def save_report(
        self,
        report: ContractReport,
        source_text: str,
        source_name: str | None = None,
        source_document: ExtractedDocument | None = None,
        source_file_bytes: bytes | None = None,
    ) -> dict[str, Any]:
        artifact = None
        if source_file_bytes is not None:
            artifact = self._artifacts.save_artifact(
                _artifact_name(source_name, source_document),
                source_file_bytes,
            )

        record = {
            "id": uuid4().hex,
            "created_at": datetime.now(UTC).isoformat(),
            "source_name": source_name or "Pasted contract",
            "contract_type": report.contract_type,
            "overall_risk_level": report.overall_risk_level,
            "overall_risk_score": report.overall_risk_score,
            "summary": report.summary,
            "counts": _risk_counts(report.findings),
            "source_text": source_text,
            "source_backend": report.source_backend,
            "source_page_count": report.source_page_count,
            "ocr_used": report.ocr_used,
            "ocr_engine": report.ocr_engine,
            "source_document": source_document.to_dict() if source_document else None,
            "source_artifact": artifact,
            "report": report.to_dict(),
        }
        self._records.save_record(record)
        return record

    def list_reports(self) -> list[dict[str, Any]]:
        return [self._summary(record) for record in self._records.list_records()]

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        return self._records.get_record(report_id)

    def delete_report(self, report_id: str) -> bool:
        record = self._records.get_record(report_id)
        if record is None:
            return False

        deleted = self._records.delete_record(report_id)
        if deleted:
            self._artifacts.delete_artifact(record.get("source_artifact"))
            self._review_requests.delete_requests_for_report(report_id)
        return deleted

    def create_review_request(
        self,
        report_id: str,
        requester_email: str | None = None,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        record = self._records.get_record(report_id)
        if record is None:
            return None

        existing = self._review_requests.get_request_by_report_id(report_id)
        if existing is not None:
            return existing

        request_record = _review_request_from_report(
            record,
            requester_email=requester_email,
            note=note,
        )
        self._review_requests.save_request(request_record)
        return request_record

    def list_review_requests(self) -> list[dict[str, Any]]:
        return self._review_requests.list_requests()

    def _summary(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": record["id"],
            "created_at": record["created_at"],
            "source_name": record["source_name"],
            "contract_type": record["contract_type"],
            "overall_risk_level": record["overall_risk_level"],
            "overall_risk_score": record["overall_risk_score"],
            "summary": record["summary"],
            "counts": record["counts"],
            "source_backend": record.get("source_backend"),
            "source_page_count": record.get("source_page_count", 0),
            "ocr_used": record.get("ocr_used", False),
            "has_source_artifact": record.get("source_artifact") is not None,
        }


def _build_record_repository(
    configured_backend: str, path: Path
) -> RecordRepository:
    backend = resolve_store_backend(configured_backend, path)
    if backend == "sqlite":
        return SQLiteReportRepository(path)
    return JsonReportRepository(path)


def _artifact_name(
    source_name: str | None, source_document: ExtractedDocument | None
) -> str | None:
    if source_name:
        return source_name
    if source_document is not None:
        return source_document.filename
    return None


def _risk_counts(findings: list[ClauseFinding]) -> dict[str, int]:
    counts = {"red": 0, "yellow": 0, "green": 0}
    for finding in findings:
        counts[finding.risk_level] += 1
    return counts


def _review_request_from_report(
    record: dict[str, Any],
    *,
    requester_email: str | None,
    note: str | None,
) -> dict[str, Any]:
    report = record["report"]
    finding_titles = _finding_titles(report)
    return {
        "id": uuid4().hex,
        "created_at": datetime.now(UTC).isoformat(),
        "report_id": record["id"],
        "status": "requested",
        "priority": _review_priority(record),
        "source_name": record["source_name"],
        "contract_type": record["contract_type"],
        "overall_risk_level": record["overall_risk_level"],
        "overall_risk_score": record["overall_risk_score"],
        "requester_email": _clean_optional_string(requester_email, max_length=254),
        "note": _clean_optional_string(note, max_length=1200),
        "report_summary": record["summary"],
        "finding_titles": finding_titles,
        "lawyer_brief": _lawyer_brief(record, finding_titles),
    }


def _review_priority(record: dict[str, Any]) -> str:
    counts = record.get("counts") or {}
    if record["overall_risk_level"] == "high" or int(counts.get("red", 0)) > 0:
        return "high"
    if record["overall_risk_level"] == "medium" or int(counts.get("yellow", 0)) > 0:
        return "medium"
    return "normal"


def _finding_titles(report: dict[str, Any]) -> list[str]:
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        return []
    titles: list[str] = []
    for finding in findings[:6]:
        if isinstance(finding, dict) and isinstance(finding.get("title"), str):
            titles.append(finding["title"])
    return titles


def _lawyer_brief(record: dict[str, Any], finding_titles: list[str]) -> str:
    findings = ", ".join(finding_titles) if finding_titles else "No flagged findings"
    return (
        f"Local lawyer review request for {record['source_name']}. "
        f"Contract type: {record['contract_type']}. "
        f"Risk: {record['overall_risk_level']} ({record['overall_risk_score']}/100). "
        f"Key findings: {findings}. "
        "Use the saved report for evidence spans, suggested wording, and negotiation context."
    )


def _clean_optional_string(value: str | None, *, max_length: int) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_length]
