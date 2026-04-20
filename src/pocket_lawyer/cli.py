from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pocket_lawyer.analyzer import analyze_contract


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pocket-lawyer",
        description="Analyze Indian employment contract text.",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Contract text to analyze.")
    input_group.add_argument("--file", type=Path, help="Path to a UTF-8 text file.")
    parser.add_argument("--contract-type", default="employment")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON.")
    parser.add_argument("--output", type=Path, help="Optional path to write JSON report.")

    args = parser.parse_args(argv)

    try:
        text = _read_input_text(args.text, args.file)
    except OSError as exc:
        print(f"pocket-lawyer: {exc}", file=sys.stderr)
        return 2

    report = analyze_contract(text, contract_type=args.contract_type)
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


def _read_input_text(text_arg: str | None, file_arg: Path | None) -> str:
    if text_arg is not None:
        return text_arg

    if file_arg is None:
        raise OSError("Either --text or --file is required.")

    return file_arg.read_text(encoding="utf-8")
