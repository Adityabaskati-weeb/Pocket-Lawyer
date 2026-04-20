from __future__ import annotations

import json
from pathlib import Path

from pocket_lawyer.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_cli_prints_json_report(capsys) -> None:
    status = main(
        [
            "--text",
            "The employee agrees to a non-compete for 24 months after employment.",
        ]
    )

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert status == 0
    assert payload["overall_risk_level"] == "high"
    assert payload["findings"][0]["category"] == "non_compete"


def test_cli_reads_text_file(capsys) -> None:
    contract_path = ROOT / "tests" / "fixtures" / "sample_green_contract.txt"

    status = main(["--file", str(contract_path), "--compact"])

    output = capsys.readouterr().out
    payload = json.loads(output)

    assert status == 0
    assert payload["overall_risk_level"] == "low"
    assert payload["findings"][0]["risk_level"] == "green"


def test_cli_accepts_contract_type(capsys) -> None:
    status = main(
        [
            "--contract-type",
            "vendor",
            "--text",
            "The vendor has unlimited liability for all losses.",
        ]
    )

    payload = json.loads(capsys.readouterr().out)

    assert status == 0
    assert payload["contract_type"] == "vendor"
    assert payload["findings"][0]["category"] == "liability"
