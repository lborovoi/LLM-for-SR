"""Command-line interface for validation and result reproduction."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .analysis import reproduce
from .validation import EXPECTATIONS, validate_all, validate_dataset


def default_root() -> Path:
    return Path.cwd()


def parser() -> argparse.ArgumentParser:
    root = default_root()
    command = argparse.ArgumentParser(prog="llm-sr-benchmark")
    subcommands = command.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="validate locked public datasets")
    validate.add_argument(
        "--data",
        type=Path,
        default=root / "data" / "locked",
        help="directory containing sr1.csv, sr2.csv, and sr3.csv",
    )

    reproduce_command = subcommands.add_parser(
        "reproduce", help="recalculate publication result tables"
    )
    reproduce_command.add_argument(
        "--data",
        type=Path,
        default=root / "data" / "locked",
        help="directory containing the locked datasets",
    )
    reproduce_command.add_argument(
        "--output",
        type=Path,
        default=root / "results" / "reproduced",
        help="output directory for recalculated tables",
    )
    return command


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "validate":
        errors = validate_all(arguments.data)
        for review in EXPECTATIONS:
            _, summary = validate_dataset(review, arguments.data)
            print(summary)
        if errors:
            print("Validation failed:")
            for error in errors:
                print(f"- {error}")
            return 1
        print("Validation passed.")
        return 0

    errors = validate_all(arguments.data)
    if errors:
        print("Dataset validation failed; results were not generated.")
        for error in errors:
            print(f"- {error}")
        return 1
    reproduce(arguments.data, arguments.output)
    print(f"Wrote reproduced tables to {arguments.output}")
    return 0

