"""CLI: python -m src.cli <protocol_file.txt> -- prints structured JSON to stdout, and flags any
escalation criteria from the source text that the validation layer can't find in the output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from .structure import structure_protocol
from .validate import validate_escalation_coverage


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Structure an unstructured clinical protocol into a session plan + QA rubric."
    )
    parser.add_argument("protocol_file", type=Path, help="Path to a plain-text protocol file")
    parser.add_argument(
        "--model", default=None, help="Override the Claude model (default: env CLAUDE_MODEL or claude-sonnet-5)"
    )
    args = parser.parse_args()

    protocol_text = args.protocol_file.read_text(encoding="utf-8")
    result = structure_protocol(protocol_text, model=args.model)
    print(json.dumps(result.model_dump(), indent=2))

    issues = validate_escalation_coverage(protocol_text, result)
    if issues:
        print(f"\n[validation] {len(issues)} possible dropped escalation criteria:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)


if __name__ == "__main__":
    main()
