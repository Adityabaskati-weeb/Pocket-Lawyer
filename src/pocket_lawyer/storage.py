from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pocket_lawyer.models import ClauseFinding, ContractReport


DEFAULT_STORE_PATH = Path(
    os.environ.get("POCKET_LAWYER_STORE", "data/reports.json")
)


class ReportStore:
    def __init__(self, path: str | Path = DEFAULT_STORE_PATH) -> None:
        self.path = Path(path)

    def save_report(
        self,
        report: ContractReport,
        source_text: str,
        source_name: str | None = None,
    ) -> dict[str, Any]:
        records = self._load_records()
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
            "report": report.to_dict(),
        }
        records.append(record)
        self._write_records(records)
        return record

    def list_reports(self) -> list[dict[str, Any]]:
        return [self._summary(record) for record in reversed(self._load_records())]

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        for record in self._load_records():
            if record["id"] == report_id:
                return record
        return None

    def delete_report(self, report_id: str) -> bool:
        records = self._load_records()
        kept = [record for record in records if record["id"] != report_id]
        if len(kept) == len(records):
            return False
        self._write_records(kept)
        return True

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
        }

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        raw = self.path.read_text(encoding="utf-8")
        if not raw.strip():
            return []

        payload = json.loads(raw)
        if not isinstance(payload, list):
            raise ValueError("Report store must contain a JSON list.")
        return payload

    def _write_records(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def _risk_counts(findings: list[ClauseFinding]) -> dict[str, int]:
    counts = {"red": 0, "yellow": 0, "green": 0}
    for finding in findings:
        counts[finding.risk_level] += 1
    return counts
