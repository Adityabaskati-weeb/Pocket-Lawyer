from __future__ import annotations

import tempfile
import time
from pathlib import Path

from pocket_lawyer import analyze_contract, analyze_extracted_document
from pocket_lawyer.intake import build_text_document
from pocket_lawyer.storage import ReportStore


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = Path(tempfile.gettempdir()) / "pocket_lawyer_tests"


def test_report_store_saves_lists_gets_and_deletes_report() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    store_path = RUNTIME_DIR / "storage_reports.json"
    if store_path.exists():
        safe_unlink(store_path)

    store = ReportStore(store_path)
    document = build_text_document(
        "All intellectual property created outside work hours belongs to the employer.",
        backend="docling",
    )
    report = analyze_extracted_document(document)
    record = store.save_report(
        report,
        source_text=document.text,
        source_name="sample.txt",
        source_document=document,
    )

    history = store.list_reports()
    saved = store.get_report(record["id"])
    deleted = store.delete_report(record["id"])

    assert history[0]["id"] == record["id"]
    assert history[0]["counts"]["red"] == 1
    assert history[0]["source_backend"] == "docling"
    assert history[0]["has_source_artifact"] is False
    assert saved is not None
    assert saved["source_name"] == "sample.txt"
    assert saved["source_document"]["backend"] == "docling"
    assert saved["source_artifact"] is None
    assert deleted is True
    assert store.get_report(record["id"]) is None

    if store_path.exists():
        safe_unlink(store_path)


def test_report_store_creates_local_review_request_without_source_text() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    store_path = RUNTIME_DIR / "storage_review_requests.json"
    if store_path.exists():
        safe_unlink(store_path)
    review_path = RUNTIME_DIR / "storage_review_requests_review_requests.json"
    if review_path.exists():
        safe_unlink(review_path)

    store = ReportStore(store_path)
    report = analyze_contract(
        "The employee agrees to a non-compete for 24 months after employment."
    )
    record = store.save_report(
        report,
        source_text="The employee agrees to a non-compete for 24 months after employment.",
        source_name="Offer letter",
    )

    review_request = store.create_review_request(
        record["id"],
        requester_email="founder@example.com",
        note="Need a qualified lawyer to review before signing.",
    )
    duplicate_request = store.create_review_request(record["id"])
    review_requests = store.list_review_requests()

    assert review_request is not None
    assert duplicate_request is not None
    assert duplicate_request["id"] == review_request["id"]
    assert review_requests[0]["id"] == review_request["id"]
    assert review_request["report_id"] == record["id"]
    assert review_request["status"] == "requested"
    assert review_request["priority"] == "high"
    assert review_request["source_name"] == "Offer letter"
    assert review_request["requester_email"] == "founder@example.com"
    assert "Post-employment non-compete" in review_request["finding_titles"]
    assert "source_text" not in review_request
    assert "non-compete" in review_request["lawyer_brief"].lower()

    deleted = store.delete_report(record["id"])

    assert deleted is True
    assert store.list_review_requests() == []

    if store_path.exists():
        safe_unlink(store_path)
    if review_path.exists():
        safe_unlink(review_path)


def test_report_store_supports_sqlite_and_uploaded_artifacts() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    store_path = RUNTIME_DIR / "storage_reports.sqlite"
    uploads_root = RUNTIME_DIR / "storage_uploads"
    if store_path.exists():
        safe_unlink(store_path)
    safe_rmtree(uploads_root)

    store = ReportStore(store_path, uploads_root=uploads_root)
    document = build_text_document(
        "The borrower shall provide a blank cheque as security.",
        backend="docling",
    )
    report = analyze_extracted_document(document, contract_type="loan")
    record = store.save_report(
        report,
        source_text=document.text,
        source_name="loan-contract.pdf",
        source_document=document,
        source_file_bytes=b"%PDF-1.7 demo",
    )

    saved = store.get_report(record["id"])
    history = store.list_reports()
    artifact = saved["source_artifact"] if saved else None

    assert history[0]["id"] == record["id"]
    assert history[0]["has_source_artifact"] is True
    assert saved is not None
    assert artifact is not None
    assert artifact["original_filename"] == "loan-contract.pdf"
    assert artifact["byte_size"] == len(b"%PDF-1.7 demo")
    assert (uploads_root / artifact["storage_key"]).exists()

    deleted = store.delete_report(record["id"])

    assert deleted is True
    assert not (uploads_root / artifact["storage_key"]).exists()
    assert store.get_report(record["id"]) is None

    if store_path.exists():
        safe_unlink(store_path)
    safe_rmtree(uploads_root)


def test_json_store_falls_back_when_atomic_replace_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    store_path = RUNTIME_DIR / "storage_replace_fallback.json"
    if store_path.exists():
        safe_unlink(store_path)

    original_replace = Path.replace
    original_unlink = Path.unlink

    def deny_replace_once(path: Path, target: Path) -> Path:
        if path.name == "storage_replace_fallback.json.tmp":
            raise PermissionError("simulated OneDrive replace denial")
        return original_replace(path, target)

    def deny_tmp_unlink(path: Path, missing_ok: bool = False) -> None:
        if path.name == "storage_replace_fallback.json.tmp":
            raise PermissionError("simulated OneDrive temp cleanup denial")
        return original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "replace", deny_replace_once)
    monkeypatch.setattr(Path, "unlink", deny_tmp_unlink)

    store = ReportStore(store_path)
    report = analyze_contract(
        "The employee agrees to a non-compete for 24 months after employment."
    )
    record = store.save_report(
        report,
        source_text="The employee agrees to a non-compete for 24 months after employment.",
        source_name="Offer letter",
    )

    saved = store.get_report(record["id"])

    assert saved is not None
    assert saved["source_name"] == "Offer letter"

    monkeypatch.undo()
    if store_path.exists():
        safe_unlink(store_path)
    temp_path = store_path.with_suffix(".json.tmp")
    if temp_path.exists():
        safe_unlink(temp_path)


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
