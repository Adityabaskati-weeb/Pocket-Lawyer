from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Protocol


SQLITE_SUFFIXES = frozenset({".db", ".sqlite", ".sqlite3"})


class RecordRepository(Protocol):
    def save_record(self, record: dict[str, Any]) -> None: ...

    def list_records(self) -> list[dict[str, Any]]: ...

    def get_record(self, report_id: str) -> dict[str, Any] | None: ...

    def delete_record(self, report_id: str) -> bool: ...


class JsonReportRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save_record(self, record: dict[str, Any]) -> None:
        records = self._load_records()
        records.append(record)
        self._write_records(records)

    def list_records(self) -> list[dict[str, Any]]:
        return list(reversed(self._load_records()))

    def get_record(self, report_id: str) -> dict[str, Any] | None:
        for record in self._load_records():
            if record["id"] == report_id:
                return record
        return None

    def delete_record(self, report_id: str) -> bool:
        records = self._load_records()
        kept = [record for record in records if record["id"] != report_id]
        if len(kept) == len(records):
            return False
        if kept:
            self._write_records(kept)
        elif self.path.exists():
            self.path.unlink(missing_ok=True)
        return True

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
        payload = json.dumps(records, indent=2) + "\n"
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(payload, encoding="utf-8")
        _replace_or_fallback(temp_path, self.path, payload)


class SQLiteReportRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._ensure_schema()

    def save_record(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                INSERT INTO reports (
                    id,
                    created_at,
                    source_name,
                    contract_type,
                    overall_risk_level,
                    overall_risk_score,
                    summary,
                    counts_json,
                    source_text,
                    source_backend,
                    source_page_count,
                    ocr_used,
                    ocr_engine,
                    source_document_json,
                    source_artifact_json,
                    report_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["id"],
                    record["created_at"],
                    record["source_name"],
                    record["contract_type"],
                    record["overall_risk_level"],
                    record["overall_risk_score"],
                    record["summary"],
                    json.dumps(record["counts"]),
                    record["source_text"],
                    record.get("source_backend"),
                    int(record.get("source_page_count", 0)),
                    int(bool(record.get("ocr_used", False))),
                    record.get("ocr_engine"),
                    _json_or_none(record.get("source_document")),
                    _json_or_none(record.get("source_artifact")),
                    json.dumps(record["report"]),
                ),
            )

    def list_records(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    created_at,
                    source_name,
                    contract_type,
                    overall_risk_level,
                    overall_risk_score,
                    summary,
                    counts_json,
                    source_text,
                    source_backend,
                    source_page_count,
                    ocr_used,
                    ocr_engine,
                    source_document_json,
                    source_artifact_json,
                    report_json
                FROM reports
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_record(self, report_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    created_at,
                    source_name,
                    contract_type,
                    overall_risk_level,
                    overall_risk_score,
                    summary,
                    counts_json,
                    source_text,
                    source_backend,
                    source_page_count,
                    ocr_used,
                    ocr_engine,
                    source_document_json,
                    source_artifact_json,
                    report_json
                FROM reports
                WHERE id = ?
                """,
                (report_id,),
            ).fetchone()
        if row is None:
            return None
        return _record_from_row(row)

    def delete_record(self, report_id: str) -> bool:
        with closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "DELETE FROM reports WHERE id = ?",
                (report_id,),
            )
            return cursor.rowcount > 0

    def _ensure_schema(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    contract_type TEXT NOT NULL,
                    overall_risk_level TEXT NOT NULL,
                    overall_risk_score INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    counts_json TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    source_backend TEXT,
                    source_page_count INTEGER NOT NULL DEFAULT 0,
                    ocr_used INTEGER NOT NULL DEFAULT 0,
                    ocr_engine TEXT,
                    source_document_json TEXT,
                    source_artifact_json TEXT,
                    report_json TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection


def resolve_store_backend(configured_backend: str, path: Path) -> str:
    if configured_backend in {"json", "sqlite"}:
        return configured_backend
    if path.suffix.lower() in SQLITE_SUFFIXES:
        return "sqlite"
    return "json"


def _replace_or_fallback(
    temp_path: Path,
    target_path: Path,
    payload: str,
    *,
    attempts: int = 5,
    delay_seconds: float = 0.1,
) -> None:
    last_error: PermissionError | None = None
    for _ in range(attempts):
        try:
            temp_path.replace(target_path)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(delay_seconds)

    # OneDrive and Windows security tools can deny os.replace while still allowing
    # normal writes. Keep the local demo usable rather than dropping the report.
    target_path.write_text(payload, encoding="utf-8")
    try:
        temp_path.unlink(missing_ok=True)
    except PermissionError:
        return


def _record_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "source_name": row["source_name"],
        "contract_type": row["contract_type"],
        "overall_risk_level": row["overall_risk_level"],
        "overall_risk_score": row["overall_risk_score"],
        "summary": row["summary"],
        "counts": json.loads(row["counts_json"]),
        "source_text": row["source_text"],
        "source_backend": row["source_backend"],
        "source_page_count": row["source_page_count"],
        "ocr_used": bool(row["ocr_used"]),
        "ocr_engine": row["ocr_engine"],
        "source_document": _json_from_nullable(row["source_document_json"]),
        "source_artifact": _json_from_nullable(row["source_artifact_json"]),
        "report": json.loads(row["report_json"]),
    }


def _json_or_none(value: object) -> str | None:
    if value is None:
        return None
    return json.dumps(value)


def _json_from_nullable(value: object) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if not isinstance(value, str) or not value:
        return None
    return json.loads(value)
