"""CLI: python -m src.cli <protocol_file.txt> -- prints structured JSON to stdout, and flags any
escalation criteria from the source text that the validation layer can't find in the output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from .render import render_coach_plan, render_qa_checklist
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
    parser.add_argument(
        "--render",
        action="store_true",
        help="Also print the coach-facing session plan and coordinator-facing QA checklist as markdown",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write <name>_coach.md and <name>_qa.md into this directory instead of printing them",
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

    if args.render or args.out_dir:
        coach_md = render_coach_plan(result)
        qa_md = render_qa_checklist(result)

        if args.out_dir:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            stem = args.protocol_file.stem
            (args.out_dir / f"{stem}_coach.md").write_text(coach_md, encoding="utf-8")
            (args.out_dir / f"{stem}_qa.md").write_text(qa_md, encoding="utf-8")
            print(f"\nWrote {stem}_coach.md and {stem}_qa.md to {args.out_dir}", file=sys.stderr)
        else:
            print("\n\n---- COACH SESSION PLAN ----\n")
            print(coach_md)
            print("\n---- COORDINATOR QA CHECKLIST ----\n")
            print(qa_md)


if __name__ == "__main__":
    main()
