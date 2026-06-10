from __future__ import annotations

import argparse
import json
from pathlib import Path

from pocket_lawyer.evaluation import evaluate_golden_cases, load_golden_cases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "fixtures" / "golden_evaluation_cases.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Pocket Lawyer golden report evaluations."
    )
    parser.add_argument(
        "--cases",
        default=DEFAULT_CASES,
        type=Path,
        help="Path to a JSON list of golden evaluation cases.",
    )
    args = parser.parse_args()

    result = evaluate_golden_cases(load_golden_cases(args.cases))
    print(json.dumps(result, indent=2))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
