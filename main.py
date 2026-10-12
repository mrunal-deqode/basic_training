"""python3 main.py [input_file] [output_dir] [--impl function] [--strict]"""

import argparse
import sys
from pathlib import Path
from typing import Callable

from src.exceptions import BriefCheckerError
from src.report import format_failure_table, format_summary, write_reports
from src.utils import load_brief
from src.validator import validate_brief

EXIT_COMPLIANT = 0
EXIT_NON_COMPLIANT = 1
EXIT_NO_INPUT = 2
EXIT_BAD_INPUT = 3
EXIT_WRITE_ERROR = 4
EXIT_CANCELLED = 130  

IMPLEMENTATIONS: dict[str, Callable] = {
    "function": validate_brief,
}

PROMPT = "Enter the path to a brief JSON file (or q to quit): "


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Check a project brief against the 10-section blueprint.",
    )
    parser.add_argument(
        "input_file", nargs="?",
        help="path to the brief JSON file (asked for if left out)",
    )
    parser.add_argument(
        "output_dir", nargs="?", default="output",
        help="folder for the report files (default: output)",
    )
    parser.add_argument(
        "--impl", choices=list(IMPLEMENTATIONS), default="function",
        help="which implementation to run (default: function)",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="treat warnings (such as extra fields) as errors",
    )
    return parser.parse_args(argv)


def ask_for_path() -> str | None:
    path = None

    while True:
        try:
            answer = input(PROMPT).strip()
        except EOFError:  
            break

        if answer.lower() in ("q", "quit"):
            break

        if answer == "":  
            continue

        if Path(answer).is_file():
            path = answer
            break

        print(f"  File not found: {answer}. Please try again.")

    return path


def run_check(
    input_path: str,
    output_dir: str,
    implementation: str = "function",
    strict: bool = False,
) -> int:
    name = Path(input_path).name
    validate = IMPLEMENTATIONS[implementation]

    try:
        data = load_brief(input_path)
        results = validate(data, file_name=name, strict=strict)
    except BriefCheckerError as error:
        print(f"Cannot check '{name}': {error}", file=sys.stderr)
        return EXIT_BAD_INPUT
    else:
        
        try:
            summary, csv_path, json_path = write_reports(
                results, output_dir, name
            )
        except OSError as error:
            print(f"Could not write the reports: {error}", file=sys.stderr)
            return EXIT_WRITE_ERROR

        print(format_summary(summary))
        print()
        print(format_failure_table(results))
        print()
        print("Reports written:")
        print(f"  {csv_path}")
        print(f"  {json_path}")

        if summary["verdict"] == "NON-COMPLIANT":
            return EXIT_NON_COMPLIANT
        return EXIT_COMPLIANT
    finally:
        print(f"Finished checking '{name}'.")


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)

    try:
        input_path = args.input_file
        if input_path is None:
            input_path = ask_for_path()
        if input_path is None:
            print("No input file given. Goodbye.")
            return EXIT_NO_INPUT

        return run_check(input_path, args.output_dir, args.impl, args.strict)
    except KeyboardInterrupt:  
        print("\nCancelled by the user.")
        return EXIT_CANCELLED


if __name__ == "__main__":
    sys.exit(main())