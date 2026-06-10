from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from pocket_lawyer.analysis import analyze_contract, analyze_extracted_document
from pocket_lawyer.analysis.contract_type_detection import detect_contract_type_for_upload
from pocket_lawyer.intake import IntakeError, build_contract_submission
from pocket_lawyer.settings import get_settings
from pocket_lawyer.storage import ReportStore


CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}


class PocketLawyerHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False


class PocketLawyerHandler(BaseHTTPRequestHandler):
    server_version = "PocketLawyerHTTP/0.1"

    def do_GET(self) -> None:
        path = self._path()

        if path == "/health":
            self._send_json({"status": "ok"})
            return

        if path == "/contracts":
            self._send_json({"contracts": self.server.report_store.list_reports()})
            return

        if path == "/review-requests":
            self._send_json(
                {"review_requests": self.server.report_store.list_review_requests()}
            )
            return

        if path.startswith("/contracts/"):
            self._handle_contract_get(path.removeprefix("/contracts/"))
            return

        if path in {"/", "/index.html"}:
            self._send_file(self.server.web_root / "index.html")
            return

        if path.startswith("/static/"):
            self._send_static_file(path.removeprefix("/static/"))
            return

        self._send_json(
            {"error": "Not found", "supported_paths": ["/health", "/analyze"]},
            status=HTTPStatus.NOT_FOUND,
        )

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self) -> None:
        path = self._path()

        if path == "/analyze":
            self._handle_analyze()
            return

        if path == "/contracts":
            self._handle_contract_create()
            return

        if path.startswith("/contracts/") and path.endswith("/review-request"):
            self._handle_review_request_create(path)
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        path = self._path()

        if not path.startswith("/contracts/"):
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        report_id = path.removeprefix("/contracts/").strip("/")
        deleted = self.server.report_store.delete_report(report_id)
        if not deleted:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        self._send_json({"deleted": True, "id": report_id})

    def _handle_analyze(self) -> None:
        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        text = payload.get("text")
        contract_type = payload.get("contract_type", "employment")
        if not isinstance(text, str) or not text.strip():
            self._send_json(
                {"error": "Request JSON must include non-empty string field 'text'."},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        if not isinstance(contract_type, str) or not contract_type.strip():
            contract_type = "employment"

        report = analyze_contract(text, contract_type=contract_type)
        self._send_json(report.to_dict())

    def _handle_contract_create(self) -> None:
        try:
            payload = self._read_json_body()
            submission = build_contract_submission(payload)
        except (ValueError, IntakeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        contract_type = payload.get("contract_type", "employment")
        if submission.source_file_bytes is not None:
            contract_type = detect_contract_type_for_upload(
                submission.document,
                source_name=submission.source_name,
                requested_contract_type=contract_type,
            )
        elif not isinstance(contract_type, str) or not contract_type.strip():
            contract_type = "employment"

        report = analyze_extracted_document(
            submission.document,
            contract_type=contract_type,
        )
        record = self.server.report_store.save_report(
            report,
            source_text=submission.document.text,
            source_name=submission.source_name,
            source_document=submission.document,
            source_file_bytes=submission.source_file_bytes,
        )
        self._send_json(
            {
                "record": self.server.report_store._summary(record),
                "report": report.to_dict(),
                "extracted_text": submission.document.text,
            },
            status=HTTPStatus.CREATED,
        )

    def _handle_contract_get(self, report_id: str) -> None:
        clean_id = report_id.strip("/")
        if not clean_id:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        record = self.server.report_store.get_report(clean_id)
        if not record:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        self._send_json(record)

    def _handle_review_request_create(self, path: str) -> None:
        parts = path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "contracts" or parts[2] != "review-request":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            payload = self._read_optional_json_body()
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        review_request = self.server.report_store.create_review_request(
            parts[1],
            requester_email=payload.get("requester_email"),
            note=payload.get("note"),
        )
        if review_request is None:
            self._send_json({"error": "Report not found"}, status=HTTPStatus.NOT_FOUND)
            return

        self._send_json(
            {"review_request": review_request},
            status=HTTPStatus.CREATED,
        )

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _path(self) -> str:
        return urlsplit(self.path).path

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("Request body must be JSON.")

        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc

        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _read_optional_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        return self._read_json_body()

    def _send_json(
        self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_static_file(self, relative_path: str) -> None:
        candidate = (self.server.web_root / "static" / unquote(relative_path)).resolve()
        static_root = (self.server.web_root / "static").resolve()

        if static_root not in candidate.parents and candidate != static_root:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        self._send_file(candidate)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        content_type = CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(
    host: str | None = None,
    port: int | None = None,
    store_path: str | Path | None = None,
    uploads_root: str | Path | None = None,
) -> PocketLawyerHTTPServer:
    settings = get_settings()
    server = PocketLawyerHTTPServer(
        (
            host if host is not None else settings.default_host,
            port if port is not None else settings.default_port,
        ),
        PocketLawyerHandler,
    )
    server.report_store = (
        ReportStore(store_path, uploads_root=uploads_root)
        if store_path
        else ReportStore(uploads_root=uploads_root)
    )
    server.web_root = settings.web_root
    return server


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Run the Pocket Lawyer local API.")
    parser.add_argument("--host", default=settings.default_host)
    parser.add_argument("--port", default=settings.default_port, type=int)
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port)
    print(f"Pocket Lawyer running at http://{args.host}:{args.port}")
    print("Open the URL in a browser, or POST /analyze with JSON: {\"text\": \"...\"}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Pocket Lawyer API.")
    finally:
        server.server_close()

    return 0
