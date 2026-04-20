from __future__ import annotations

from pathlib import Path

from pocket_lawyer import analyze_contract
from pocket_lawyer.storage import ReportStore


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / "tests" / "runtime"


def test_report_store_saves_lists_gets_and_deletes_report() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    store_path = RUNTIME_DIR / "storage_reports.json"
    if store_path.exists():
        store_path.unlink()

    store = ReportStore(store_path)
    report = analyze_contract(
        "All intellectual property created outside work hours belongs to the employer."
    )
    record = store.save_report(
        report,
        source_text="All intellectual property created outside work hours belongs to the employer.",
        source_name="sample.txt",
    )

    history = store.list_reports()
    saved = store.get_report(record["id"])
    deleted = store.delete_report(record["id"])

    assert history[0]["id"] == record["id"]
    assert history[0]["counts"]["red"] == 1
    assert saved is not None
    assert saved["source_name"] == "sample.txt"
    assert deleted is True
    assert store.get_report(record["id"]) is None

    if store_path.exists():
        store_path.unlink()
