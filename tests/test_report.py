"""Unit tests for src/report.py: scoring, verdicts, writers and text."""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.report import (
    CSV_COLUMNS,
    build_summary,
    calculate_score,
    count_results,
    format_failure_table,
    format_summary,
    get_verdict,
    make_output_paths,
    write_csv,
    write_json,
    write_reports,
)


def make_row(
    status: str = "PASS",
    severity: str = "info",
    section: str = "section 1",
    check: str = "heading",
    message: str = "ok",
) -> dict[str, str]:
    """Build one result row by hand, so these tests need no validator.

    Args:
        status: "PASS" or "FAIL".
        severity: "info", "warning" or "error".
        section: The section label.
        check: The check name.
        message: The message text.

    Returns:
        A row with all six keys.
    """
    return {
        "file": "x.json",
        "section": section,
        "check": check,
        "status": status,
        "severity": severity,
        "message": message,
    }


class TestScoring(unittest.TestCase):
    """Counting, score and verdict."""

    def test_count_results(self) -> None:
        """Passes, failures, errors and warnings are counted apart."""
        rows = [
            make_row(),
            make_row(),
            make_row("FAIL", "error"),
            make_row("FAIL", "warning"),
        ]
        self.assertEqual(
            count_results(rows),
            {"total": 4, "passed": 2, "failed": 2, "errors": 1,
             "warnings": 1},
        )

    def test_calculate_score(self) -> None:
        """The score is a rounded percentage and never divides by zero."""
        self.assertEqual(calculate_score(106, 106), 100.0)
        self.assertEqual(calculate_score(1, 3), 33.3)
        self.assertEqual(calculate_score(0, 0), 0.0)

    def test_get_verdict(self) -> None:
        """No checks, no errors and some errors give three verdicts."""
        self.assertEqual(get_verdict(0, 0), "NOT CHECKED")
        self.assertEqual(get_verdict(10, 0), "COMPLIANT")
        self.assertEqual(get_verdict(10, 2), "NON-COMPLIANT")

    def test_warnings_do_not_make_a_brief_non_compliant(self) -> None:
        """A warning lowers the score but not the verdict."""
        rows = [make_row(), make_row("FAIL", "warning")]
        summary = build_summary(rows, "x.json")

        self.assertEqual(summary["verdict"], "COMPLIANT")
        self.assertEqual(summary["score"], 50.0)

    def test_build_summary_values(self) -> None:
        """The summary dictionary holds every expected value."""
        rows = [make_row(), make_row(), make_row(), make_row("FAIL", "error")]
        summary = build_summary(rows, "demo.json")

        self.assertEqual(
            summary,
            {
                "file": "demo.json",
                "total_checks": 4,
                "passed": 3,
                "failed": 1,
                "errors": 1,
                "warnings": 0,
                "score": 75.0,
                "verdict": "NON-COMPLIANT",
            },
        )


class TestWriters(unittest.TestCase):
    """Writing the CSV and JSON files."""

    def setUp(self) -> None:
        """Create a temporary folder and two sample rows."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)
        self.rows = [
            make_row(),
            make_row("FAIL", "error", "section 4", "type",
                     'Said "no", twice'),
        ]

    def tearDown(self) -> None:
        """Delete the temporary folder and everything in it."""
        self.temp_dir.cleanup()

    def test_make_output_paths(self) -> None:
        """Report file names are built from the brief's file name."""
        csv_path, json_path = make_output_paths("out", "sample_data/a.json")

        self.assertEqual(csv_path, Path("out/a_report.csv"))
        self.assertEqual(json_path, Path("out/a_report.json"))

    def test_csv_round_trip(self) -> None:
        """Rows written to CSV read back unchanged, commas and quotes too."""
        path = write_csv(self.rows, self.folder / "r.csv")

        with open(path, newline="", encoding="utf-8") as file:
            rows_back = list(csv.DictReader(file))
        self.assertEqual(rows_back, self.rows)

    def test_csv_header_and_extra_keys(self) -> None:
        """The header follows CSV_COLUMNS and unknown keys are ignored."""
        rows = [{**self.rows[0], "debug": "extra"}]
        path = write_csv(rows, self.folder / "r.csv")

        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(first_line, ",".join(CSV_COLUMNS))

    def test_csv_creates_missing_folders(self) -> None:
        """Folders on the way to the file are created automatically."""
        path = write_csv(self.rows, self.folder / "a" / "b" / "r.csv")
        self.assertTrue(path.is_file())

    def test_json_round_trip(self) -> None:
        """The JSON file holds the summary and every row."""
        summary = build_summary(self.rows, "x.json")
        path = write_json(summary, self.rows, self.folder / "r.json")

        with open(path, encoding="utf-8") as file:
            loaded = json.load(file)
        self.assertEqual(loaded, {"summary": summary, "results": self.rows})

    def test_json_keeps_non_ascii_text(self) -> None:
        """Characters such as the rupee sign are not turned into escapes."""
        rows = [make_row(message="Fee: ₹500")]
        path = write_json({}, rows, self.folder / "r.json")
        self.assertIn("₹500", path.read_text(encoding="utf-8"))

    def test_write_reports_returns_summary_and_paths(self) -> None:
        """write_reports writes both files and reports what it did."""
        summary, csv_path, json_path = write_reports(
            self.rows, self.folder, "demo.json"
        )

        self.assertEqual(summary["file"], "demo.json")
        self.assertEqual(csv_path.name, "demo_report.csv")
        self.assertTrue(csv_path.is_file())
        self.assertTrue(json_path.is_file())

    def test_unwritable_location_raises_oserror(self) -> None:
        """A file standing where a folder is needed raises OSError."""
        blocker = self.folder / "blocker"
        blocker.write_text("I am a file, not a folder", encoding="utf-8")

        with self.assertRaises(OSError):
            write_csv(self.rows, blocker / "r.csv")


class TestFormatting(unittest.TestCase):
    """The text printed on the screen."""

    def test_format_summary(self) -> None:
        """The summary text shows the file, score and verdict."""
        rows = [make_row(), make_row(), make_row(), make_row("FAIL", "error")]
        text = format_summary(build_summary(rows, "demo.json"))

        self.assertIn("File    : demo.json", text)
        self.assertIn("Score   : 75.0%", text)
        self.assertIn("Verdict : NON-COMPLIANT", text)

    def test_failure_table_with_failures(self) -> None:
        """The table has a header, a rule line and one line per failure."""
        rows = [
            make_row(),
            make_row("FAIL", "error", "section 3", "heading", "Bad heading"),
        ]
        lines = format_failure_table(rows).splitlines()

        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("SECTION"))
        self.assertEqual(lines[1], "-" * 70)
        self.assertTrue(lines[2].startswith("section 3    heading"))
        self.assertTrue(lines[2].endswith("Bad heading"))

    def test_failure_table_without_failures(self) -> None:
        """With nothing failed, a single short message is shown."""
        self.assertEqual(
            format_failure_table([make_row()]), "No failed checks."
        )


if __name__ == "__main__":
    unittest.main()
