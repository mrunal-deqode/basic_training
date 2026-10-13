"""Command-line entry point for the Blueprint Compliance Checker.

Usage:
    python3 main.py [input_file] [output_dir] [--impl function|oop]
                    [--strict] [--verbose]

If no input file is given, the program asks for one.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Callable

from src.exceptions import BriefCheckerError
from src.report import format_failure_table, format_summary, write_reports
from src.utils import TIMINGS, load_brief
from src.validator import validate_brief
from src.validator_oop import validate_brief_oop

# Exit codes: see the table in the README.
EXIT_COMPLIANT = 0
EXIT_NON_COMPLIANT = 1
EXIT_NO_INPUT = 2
EXIT_BAD_INPUT = 3
EXIT_WRITE_ERROR = 4
EXIT_CANCELLED = 130

# Which validator each --impl choice runs. Both have the same call shape.
IMPLEMENTATIONS: dict[str, Callable] = {
    "function": validate_brief,
    "oop": validate_brief_oop,
}

PROMPT = "Enter the path to a brief JSON file (or q to quit): "


def print_timings() -> None:
    """Print how long each decorated validation step took."""
    print()
    print("Timings (this run):")
    for name, seconds in TIMINGS.items():
        print(f"  {name:<22} {seconds * 1000:8.3f} ms")


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command-line arguments.

    Args:
        argv: The arguments to parse. None means "use the real command
            line"; tests can pass their own list instead.

    Returns:
        A Namespace with the attributes input_file, output_dir, impl,
        strict and verbose.
    """
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
    parser.add_argument(
        "--verbose", action="store_true",
        help="show debug logging and the time each step took",
    )
    return parser.parse_args(argv)


def ask_for_path() -> str | None:
    """Ask the user for a file path until it is valid or they quit.

    Returns:
        The path of an existing file, or None if the user chose to quit
        (or there is no keyboard to type on).
    """
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
    verbose: bool = False,
) -> int:
    """Check one brief, write the reports and print a summary.

    Args:
        input_path: Path to the brief JSON file.
        output_dir: Folder for the report files.
        implementation: Key into IMPLEMENTATIONS.
        strict: If True, warnings count as errors.
        verbose: If True, print the timing of each step.

    Returns:
        An exit code (see the EXIT_ constants).
    """
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

        if verbose:
            print_timings()

        if summary["verdict"] == "NON-COMPLIANT":
            return EXIT_NON_COMPLIANT
        return EXIT_COMPLIANT
    finally:
        print(f"Finished checking '{name}'.")


def main(argv: list[str] | None = None) -> int:
    """Run the program.

    Args:
        argv: Command-line arguments (None means the real ones).

    Returns:
        The exit code for the operating system.
    """
    args = parse_arguments(argv)

    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(levelname)s %(name)s: %(message)s",
        )

    try:
        input_path = args.input_file
        if input_path is None:
            input_path = ask_for_path()
        if input_path is None:
            print("No input file given. Goodbye.")
            return EXIT_NO_INPUT

        return run_check(
            input_path, args.output_dir, args.impl, args.strict, args.verbose
        )
    except KeyboardInterrupt:
        print("\nCancelled by the user.")
        return EXIT_CANCELLED


if __name__ == "__main__":
    sys.exit(main())
