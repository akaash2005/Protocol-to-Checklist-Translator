"""CLI: python -m src.cli <protocol_file.txt> -- prints structured JSON to stdout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from .structure import structure_protocol


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


if __name__ == "__main__":
    main()
