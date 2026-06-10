from __future__ import annotations

import tempfile
import time
from pathlib import Path

from pocket_lawyer import analyze_extracted_document
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
    assert saved is not None
    assert saved["source_name"] == "sample.txt"
    assert saved["source_document"]["backend"] == "docling"
    assert deleted is True
    assert store.get_report(record["id"]) is None

    if store_path.exists():
        safe_unlink(store_path)


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
