from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pocket_lawyer.analyzer import analyze_contract, analyze_extracted_document
from pocket_lawyer.intake import (
    IntakeError,
    build_text_document,
    extract_contract_document,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pocket-lawyer",
        description="Analyze Indian employment contract text.",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Contract text to analyze.")
    input_group.add_argument("--file", type=Path, help="Path to a contract file.")
    parser.add_argument("--contract-type", default="employment")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON.")
    parser.add_argument("--output", type=Path, help="Optional path to write JSON report.")

    args = parser.parse_args(argv)

    try:
        document = _read_input_document(args.text, args.file)
    except (OSError, IntakeError) as exc:
        print(f"pocket-lawyer: {exc}", file=sys.stderr)
        return 2

    report = analyze_extracted_document(document, contract_type=args.contract_type)
    indent = None if args.compact else 2
    payload = json.dumps(report.to_dict(), indent=indent)

    if args.output:
        try:
            args.output.write_text(payload + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"pocket-lawyer: {exc}", file=sys.stderr)
            return 2
    else:
        print(payload)

    return 0


def _read_input_document(text_arg: str | None, file_arg: Path | None):
    if text_arg is not None:
        return build_text_document(text_arg, backend="cli_text")

    if file_arg is None:
        raise OSError("Either --text or --file is required.")

    return extract_contract_document(file_arg.name, file_arg.read_bytes())
