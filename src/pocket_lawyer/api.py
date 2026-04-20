from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlsplit

from pocket_lawyer.analyzer import analyze_contract
from pocket_lawyer.intake import IntakeError, extract_contract_text
from pocket_lawyer.storage import ReportStore


WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}


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

        if path.startswith("/contracts/"):
            self._handle_contract_get(path.removeprefix("/contracts/"))
            return

        if path in {"/", "/index.html"}:
            self._send_file(WEB_ROOT / "index.html")
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
            text, source_name = self._contract_text_from_payload(payload)
        except (ValueError, IntakeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        contract_type = payload.get("contract_type", "employment")
        if not isinstance(contract_type, str) or not contract_type.strip():
            contract_type = "employment"

        report = analyze_contract(text, contract_type=contract_type)
        record = self.server.report_store.save_report(
            report, source_text=text, source_name=source_name
        )
        self._send_json(
            {
                "record": self.server.report_store._summary(record),
                "report": report.to_dict(),
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

    def _contract_text_from_payload(self, payload: dict[str, Any]) -> tuple[str, str]:
        text = payload.get("text")
        if isinstance(text, str) and text.strip():
            return text, _clean_source_name(payload.get("source_name")) or "Pasted contract"

        filename = payload.get("filename")
        content_base64 = payload.get("content_base64")
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Provide text or an uploaded filename.")
        if not isinstance(content_base64, str) or not content_base64.strip():
            raise ValueError("Uploaded files must include base64 content.")

        try:
            content = base64.b64decode(content_base64, validate=True)
        except ValueError as exc:
            raise ValueError("Uploaded file content must be valid base64.") from exc

        return extract_contract_text(filename, content), filename

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
        candidate = (WEB_ROOT / "static" / unquote(relative_path)).resolve()
        static_root = (WEB_ROOT / "static").resolve()

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
    host: str = "127.0.0.1",
    port: int = 8765,
    store_path: str | Path | None = None,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), PocketLawyerHandler)
    server.report_store = ReportStore(store_path) if store_path else ReportStore()
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Pocket Lawyer local API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
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


def _clean_source_name(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


if __name__ == "__main__":
    raise SystemExit(main())
