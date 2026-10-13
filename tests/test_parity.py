"""Parity tests: the two implementations must give identical results.

Every "variant" below takes the valid brief and breaks it in one way.
Each variant is run through both validators, with every combination of
the strict and skip_coverage options, and the rows must be equal.

Run all tests from the project root with:
    python -m unittest discover -v
"""

import contextlib
import io
import itertools
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

from main import main
from src.report import build_summary, write_reports
from src.utils import load_brief
from src.validator import validate_brief
from src.validator_oop import BriefValidator, validate_brief_oop
from tests.helpers import SAMPLE_DIR, failures, load_sample


# ---------------------------------------------------------------------------
# Breakages. Each function changes a brief IN PLACE in one particular way.
# ---------------------------------------------------------------------------
def drop_last_section(brief: dict[str, Any]) -> None:
    """Remove section 10."""
    brief["sections"].pop()


def add_extra_section(brief: dict[str, Any]) -> None:
    """Add an unexpected 11th section."""
    brief["sections"].append(
        {"number": 11, "heading": "Bonus Ideas", "content": {}}
    )


def remove_all_sections(brief: dict[str, Any]) -> None:
    """Empty the sections list."""
    brief["sections"].clear()


def keep_three_sections(brief: dict[str, Any]) -> None:
    """Keep only the first three sections."""
    del brief["sections"][3:]


def wrong_heading_text(brief: dict[str, Any]) -> None:
    """Give section 3 a heading that does not match."""
    brief["sections"][2]["heading"] = "Output Spec"


def wrong_capitals(brief: dict[str, Any]) -> None:
    """Write section 5's heading in lower case."""
    brief["sections"][4]["heading"] = "core task"


def extra_spaces(brief: dict[str, Any]) -> None:
    """Put spaces around section 1's heading."""
    brief["sections"][0]["heading"] = "  Business Scenario "


def number_prefix(brief: dict[str, Any]) -> None:
    """Put a number in front of section 2's heading."""
    brief["sections"][1]["heading"] = "2. Input Specification"


def swap_sections(brief: dict[str, Any]) -> None:
    """Swap sections 3 and 4."""
    sections = brief["sections"]
    sections[2], sections[3] = sections[3], sections[2]


def missing_field(brief: dict[str, Any]) -> None:
    """Remove the 'role' field from section 1."""
    del brief["sections"][0]["content"]["role"]


def wrong_type(brief: dict[str, Any]) -> None:
    """Make 'assumptions' text instead of a list."""
    brief["sections"][3]["content"]["assumptions"] = "just text"


def none_value(brief: dict[str, Any]) -> None:
    """Set 'role' to None."""
    brief["sections"][0]["content"]["role"] = None


def too_few_items(brief: dict[str, Any]) -> None:
    """Give section 7 only two failure cases."""
    brief["sections"][6]["content"]["failure_cases"] = ["a", "b"]


def too_many_items(brief: dict[str, Any]) -> None:
    """Give section 9 five stretch goals."""
    brief["sections"][8]["content"]["goals"] = ["goal"] * 5


def empty_content(brief: dict[str, Any]) -> None:
    """Empty section 6's content."""
    brief["sections"][5]["content"] = {}


def extra_field(brief: dict[str, Any]) -> None:
    """Add an unexpected field to section 1."""
    brief["sections"][0]["content"]["notes"] = "hello"


def blank_nested_value(brief: dict[str, Any]) -> None:
    """Blank a value inside section 2's nested 'fields'."""
    brief["sections"][1]["content"]["fields"]["appointment_id"] = ""


def blank_list_item(brief: dict[str, Any]) -> None:
    """Blank the second assumption."""
    brief["sections"][3]["content"]["assumptions"][1] = "   "


def lose_recursion_topic(brief: dict[str, Any]) -> None:
    """Remove the only mention of recursion."""
    steps = brief["sections"][4]["content"]["steps"]
    steps[6] = "Apply lambda, map(), filter() and reduce to the totals."


def kitchen_sink(brief: dict[str, Any]) -> None:
    """Combine several breakages that do not interfere with each other."""
    wrong_heading_text(brief)
    missing_field(brief)
    wrong_type(brief)
    too_few_items(brief)
    extra_field(brief)
    blank_nested_value(brief)


# Name -> function, built from the function names themselves.
VARIANTS = {
    mutate.__name__: mutate
    for mutate in (
        drop_last_section, add_extra_section, remove_all_sections,
        keep_three_sections, wrong_heading_text, wrong_capitals,
        extra_spaces, number_prefix, swap_sections, missing_field,
        wrong_type, none_value, too_few_items, too_many_items,
        empty_content, extra_field, blank_nested_value, blank_list_item,
        lose_recursion_topic, kitchen_sink,
    )
}

# All four combinations: strict on/off times skip_coverage on/off.
OPTION_SETS = [
    {"strict": strict, "skip_coverage": skip}
    for strict, skip in itertools.product((False, True), repeat=2)
]

# Input shapes that must raise an exception (not produce rows).
BAD_SHAPES = [
    ["a list"],
    {"title": "x"},
    {"sections": "text"},
    {"sections": ["oops"]},
    {"sections": [{"heading": "A"}]},
    {"sections": [{"heading": 5, "content": {}}]},
    {"sections": [{"heading": "A", "content": "text"}]},
]

def broken_brief(mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    """Load the valid brief and apply one breakage to it.

    Args:
        mutate: One of the breakage functions above.

    Returns:
        The broken brief, as a brand-new dictionary.
    """
    brief = load_sample("valid_brief.json")
    mutate(brief)
    return brief


def outcome(call: Callable[[], Any]) -> tuple:
    """Run a function and describe what happened, even if it raised.

    Catching every exception is acceptable HERE, because the test needs to
    compare errors as well as results.

    Args:
        call: A function that takes no arguments.

    Returns:
        ("rows", result) if it worked, or ("error", type name, message).
    """
    try:
        return ("rows", call())
    except Exception as error:  # noqa: BLE001 - deliberate, see docstring
        return ("error", type(error).__name__, str(error))


def run_main(*argv: str) -> tuple[int, str, str]:
    """Run main.py's main() and capture what it printed.

    Args:
        *argv: The command-line arguments.

    Returns:
        A tuple (exit code, text on stdout, text on stderr).
    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestParity(unittest.TestCase):
    """Both implementations must agree on everything."""

    def test_every_variant_matches(self) -> None:
        """20 broken briefs x 4 option combinations give equal rows."""
        for name, mutate in VARIANTS.items():
            brief = broken_brief(mutate)
            for options in OPTION_SETS:
                with self.subTest(variant=name, **options):
                    rows_function = validate_brief(brief, "x.json", **options)
                    rows_oop = validate_brief_oop(brief, "x.json", **options)

                    self.assertEqual(rows_function, rows_oop)

    def test_every_variant_actually_breaks_something(self) -> None:
        """Guard: a breakage that changes nothing would prove nothing."""
        for name, mutate in VARIANTS.items():
            with self.subTest(variant=name):
                rows = validate_brief(broken_brief(mutate), "x.json")
                self.assertNotEqual(failures(rows), [])

    def test_sample_files_match(self) -> None:
        """Every file in sample_data/ gives the same rows or the same error."""
        paths = sorted(SAMPLE_DIR.glob("*.json"))
        self.assertGreaterEqual(len(paths), 5)

        for path in paths:
            with self.subTest(file=path.name):
                from_functions = outcome(
                    lambda: validate_brief(load_brief(path), path.name)
                )
                from_classes = outcome(
                    lambda: validate_brief_oop(load_brief(path), path.name)
                )
                self.assertEqual(from_functions, from_classes)

    def test_exceptions_match(self) -> None:
        """Bad shapes and bad options give the same error type and text."""
        for data in BAD_SHAPES:
            with self.subTest(data=data):
                from_functions = outcome(lambda: validate_brief(data))
                from_classes = outcome(lambda: validate_brief_oop(data))

                self.assertEqual(from_functions[0], "error")
                self.assertEqual(from_functions, from_classes)

        brief = load_sample("valid_brief.json")
        with self.subTest(case="unknown option"):
            from_functions = outcome(
                lambda: validate_brief(brief, skip_coveage=True)
            )
            from_classes = outcome(
                lambda: validate_brief_oop(brief, skip_coveage=True)
            )
            self.assertEqual(from_functions[0], "error")
            self.assertEqual(from_functions, from_classes)

    def test_summary_matches(self) -> None:
        """The report object's summary equals the shared build_summary."""
        brief = broken_brief(kitchen_sink)

        report = BriefValidator(brief, "x.json").validate()
        expected = build_summary(validate_brief(brief, "x.json"), "x.json")

        self.assertEqual(report.summary(), expected)

    def test_report_files_are_identical(self) -> None:
        """The CSV and JSON text written from either rows is the same."""
        brief = broken_brief(kitchen_sink)
        rows_function = validate_brief(brief, "x.json")
        rows_oop = validate_brief_oop(brief, "x.json")

        with tempfile.TemporaryDirectory() as folder:
            _, csv_f, json_f = write_reports(
                rows_function, Path(folder) / "function", "x.json"
            )
            _, csv_o, json_o = write_reports(
                rows_oop, Path(folder) / "oop", "x.json"
            )

            self.assertEqual(
                csv_f.read_text(encoding="utf-8"),
                csv_o.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                json_f.read_text(encoding="utf-8"),
                json_o.read_text(encoding="utf-8"),
            )

    def test_main_output_and_exit_codes_match(self) -> None:
        """main.py behaves the same with --impl function and --impl oop."""
        paths = [str(path) for path in sorted(SAMPLE_DIR.glob("*.json"))]
        paths.append(str(SAMPLE_DIR / "does_not_exist.json"))

        with tempfile.TemporaryDirectory() as folder:
            for path in paths:
                for extra in ([], ["--strict"]):
                    with self.subTest(file=Path(path).name, extra=extra):
                        from_functions = run_main(
                            path, folder, "--impl", "function", *extra
                        )
                        from_classes = run_main(
                            path, folder, "--impl", "oop", *extra
                        )
                        self.assertEqual(from_functions, from_classes)


if __name__ == "__main__":
    unittest.main()
