from __future__ import annotations

import base64
import json
import os
import threading
import time
import tempfile
from pathlib import Path
from urllib import request
from urllib.error import HTTPError

from pocket_lawyer.api import create_server
from pocket_lawyer.settings import get_settings


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = Path(tempfile.gettempdir()) / "pocket_lawyer_tests"


def test_health_endpoint_returns_ok() -> None:
    with running_test_server() as base_url:
        with request.urlopen(f"{base_url}/health", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

    assert payload == {"status": "ok"}


def test_root_serves_web_app() -> None:
    with running_test_server() as base_url:
        with request.urlopen(f"{base_url}/?v=test", timeout=5) as response:
            html = response.read().decode("utf-8")
            content_type = response.headers["Content-Type"]

    assert "text/html" in content_type
    assert "Legal Help. In Your Pocket." in html
    assert "/static/pocket-lawyer-hero.png" in html
    assert "image-hero" in html
    assert "luxury-dock" in html
    assert "proof-grid" in html
    assert "Drop A Contract File" in html
    assert "File Readiness" in html
    assert 'id="upload-status"' in html
    assert 'id="upload-status-title"' in html
    assert "renderUploadStatus" in html
    assert "formatFileSize" in html
    assert "Initializing Sequence" not in html
    assert "Know the traps before ink dries." not in html
    assert "From dense clause to confident next move." not in html
    assert "motion-scene" not in html
    assert "initMotionScene" not in html
    assert "hero-preview" not in html
    assert "signal-cloud" not in html
    assert "scroll-cue" not in html
    assert "IP RIGHTS" not in html
    assert "fal-ai" not in html
    assert "FAL_KEY" not in html
    assert "Check your contract before you sign." in html
    assert 'value="loan"' in html
    assert "contract-pill" in html
    assert "score-ring" in html
    assert "Local funding demo map" not in html
    assert "Demo prototype" not in html
    assert "Production roadmap" not in html
    assert "AI Review Status" in html
    assert 'id="ai-review-status"' in html
    assert "renderAiReview" in html
    assert "formatAnalysisMethod" in html
    assert "Founder offer letter" in html
    assert "function renderReport" in html
    assert "/static/app.js" not in html
    assert "/static/styles.css" not in html


def test_static_javascript_is_served() -> None:
    with running_test_server() as base_url:
        with request.urlopen(f"{base_url}/static/app.js?v=test", timeout=5) as response:
            javascript = response.read().decode("utf-8")
            content_type = response.headers["Content-Type"]

    assert "application/javascript" in content_type
    assert 'fetch("/contracts"' in javascript


def test_analyze_endpoint_returns_contract_report() -> None:
    with running_test_server() as base_url:
        payload = json.dumps(
            {
                "text": (
                    "All intellectual property created outside work hours belongs "
                    "to the employer."
                )
            }
        ).encode("utf-8")
        http_request = request.Request(
            f"{base_url}/analyze",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with request.urlopen(http_request, timeout=5) as response:
            report = json.loads(response.read().decode("utf-8"))

    assert report["overall_risk_level"] == "high"
    assert report["findings"][0]["title"] == "Broad IP ownership"


def test_analyze_endpoint_rejects_missing_text() -> None:
    status = None
    payload = {}

    with running_test_server() as base_url:
        http_request = request.Request(
            f"{base_url}/analyze",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            request.urlopen(http_request, timeout=5)
        except HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            status = exc.code

    assert status == 400
    assert "text" in payload["error"]


def test_contract_create_persists_report_and_lists_history() -> None:
    store_path = RUNTIME_DIR / "api_contracts.json"

    with running_test_server(store_path) as base_url:
        create_request = request.Request(
            f"{base_url}/contracts",
            data=json.dumps(
                {
                    "text": "The employee agrees to a non-compete for 24 months.",
                    "source_name": "Offer letter",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(create_request, timeout=5) as response:
            created = json.loads(response.read().decode("utf-8"))

        with request.urlopen(f"{base_url}/contracts", timeout=5) as response:
            history = json.loads(response.read().decode("utf-8"))

        report_id = created["record"]["id"]
        with request.urlopen(f"{base_url}/contracts/{report_id}", timeout=5) as response:
            saved = json.loads(response.read().decode("utf-8"))

    assert created["record"]["source_name"] == "Offer letter"
    assert created["report"]["overall_risk_level"] == "high"
    assert history["contracts"][0]["id"] == report_id
    assert saved["report"]["findings"][0]["category"] == "non_compete"


def test_contract_create_uses_selected_contract_type() -> None:
    store_path = RUNTIME_DIR / "api_contract_types.json"

    with running_test_server(store_path) as base_url:
        create_request = request.Request(
            f"{base_url}/contracts",
            data=json.dumps(
                {
                    "contract_type": "loan",
                    "text": "The borrower shall provide a blank cheque as security.",
                    "source_name": "Loan draft",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(create_request, timeout=5) as response:
            created = json.loads(response.read().decode("utf-8"))

    assert created["report"]["contract_type"] == "loan"
    assert created["report"]["findings"][0]["category"] == "security"


def test_contract_create_accepts_base64_text_file() -> None:
    store_path = RUNTIME_DIR / "api_uploads.json"
    encoded = base64.b64encode(
        b"Both parties may terminate this agreement by giving 30 days notice."
    ).decode("ascii")

    with running_test_server(store_path) as base_url:
        create_request = request.Request(
            f"{base_url}/contracts",
            data=json.dumps(
                {
                    "filename": "contract.txt",
                    "content_base64": encoded,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(create_request, timeout=5) as response:
            created = json.loads(response.read().decode("utf-8"))

        report_id = created["record"]["id"]
        with request.urlopen(f"{base_url}/contracts/{report_id}", timeout=5) as response:
            saved = json.loads(response.read().decode("utf-8"))

    assert created["record"]["source_name"] == "contract.txt"
    assert created["report"]["overall_risk_level"] == "low"
    assert created["report"]["findings"][0]["risk_level"] == "green"
    assert created["record"]["has_source_artifact"] is True
    assert saved["source_artifact"]["original_filename"] == "contract.txt"


def test_create_server_allows_ephemeral_port(monkeypatch) -> None:
    os.environ["POCKET_LAWYER_PORT"] = "900"
    get_settings.cache_clear()
    try:
        server = create_server("127.0.0.1", 0)
    finally:
        os.environ.pop("POCKET_LAWYER_PORT", None)
        get_settings.cache_clear()

    try:
        assert server.server_address[1] != 900
    finally:
        server.server_close()


class running_test_server:
    def __init__(self, store_path: Path | None = None) -> None:
        self.store_path = store_path or (RUNTIME_DIR / "test_reports.json")
        self.uploads_root = RUNTIME_DIR / "uploads"
        self._saved_env: dict[str, str | None] = {}

    def __enter__(self) -> str:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.uploads_root.mkdir(parents=True, exist_ok=True)
        if self.store_path.exists():
            safe_unlink(self.store_path)

        self._suspend_llm_env()
        self.server = create_server(
            "127.0.0.1",
            0,
            store_path=self.store_path,
            uploads_root=self.uploads_root,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def __exit__(self, exc_type, exc, tb) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self._restore_llm_env()
        if self.store_path.exists():
            safe_unlink(self.store_path)
        safe_rmtree(self.uploads_root)

    def _suspend_llm_env(self) -> None:
        keys = [
            "POCKET_LAWYER_ENABLE_LLM",
            "POCKET_LAWYER_LLM_PROVIDER",
            "POCKET_LAWYER_LLM_MODEL",
            "POCKET_LAWYER_LLM_API_BASE",
            "POCKET_LAWYER_LLM_API_KEY",
            "POCKET_LAWYER_OPENAI_API_KEY",
            "OPENAI_API_KEY",
        ]
        self._saved_env = {key: os.environ.get(key) for key in keys}
        for key in keys:
            os.environ.pop(key, None)
        get_settings.cache_clear()

    def _restore_llm_env(self) -> None:
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        get_settings.cache_clear()


def safe_unlink(path: Path, attempts: int = 5, delay_seconds: float = 0.1) -> None:
    last_error: PermissionError | None = None
    for _ in range(attempts):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error


def safe_rmtree(path: Path) -> None:
    if not path.exists():
        return
    for child in path.iterdir():
        if child.is_dir():
            safe_rmtree(child)
        else:
            safe_unlink(child)
    path.rmdir()
