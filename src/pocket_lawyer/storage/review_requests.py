from __future__ import annotations

from contextlib import closing
import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol

from pocket_lawyer.storage.records import _replace_or_fallback, resolve_store_backend


class ReviewRequestRepository(Protocol):
    def save_request(self, request_record: dict[str, Any]) -> None: ...

    def list_requests(self) -> list[dict[str, Any]]: ...

    def get_request_by_report_id(self, report_id: str) -> dict[str, Any] | None: ...


class JsonReviewRequestRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def save_request(self, request_record: dict[str, Any]) -> None:
        requests = self._load_requests()
        requests.append(request_record)
        self._write_requests(requests)

    def list_requests(self) -> list[dict[str, Any]]:
        return list(reversed(self._load_requests()))

    def get_request_by_report_id(self, report_id: str) -> dict[str, Any] | None:
        for request_record in self.list_requests():
            if request_record["report_id"] == report_id:
                return request_record
        return None

    def _load_requests(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        raw = self.path.read_text(encoding="utf-8")
        if not raw.strip():
            return []

        payload = json.loads(raw)
        if not isinstance(payload, list):
            raise ValueError("Review request store must contain a JSON list.")
        return payload

    def _write_requests(self, requests: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(requests, indent=2) + "\n"
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(payload, encoding="utf-8")
        _replace_or_fallback(temp_path, self.path, payload)


class SQLiteReviewRequestRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._ensure_schema()

    def save_request(self, request_record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                INSERT INTO review_requests (
                    id,
                    created_at,
                    report_id,
                    status,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    request_record["id"],
                    request_record["created_at"],
                    request_record["report_id"],
                    request_record["status"],
                    json.dumps(request_record),
                ),
            )

    def list_requests(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM review_requests
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def get_request_by_report_id(self, report_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM review_requests
                WHERE report_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (report_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload_json"])

    def _ensure_schema(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS review_requests (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection


def build_review_request_repository(
    configured_backend: str,
    path: Path,
) -> ReviewRequestRepository:
    backend = resolve_store_backend(configured_backend, path)
    if backend == "sqlite":
        return SQLiteReviewRequestRepository(path)
    return JsonReviewRequestRepository(review_request_path(path))


def review_request_path(path: Path) -> Path:
    if path.suffix:
        return path.with_name(f"{path.stem}_review_requests.json")
    return path.with_name(f"{path.name}_review_requests.json")
