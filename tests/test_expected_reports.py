"""Golden-file tests: fresh reports must equal the saved expected reports.

The expected reports live in sample_data/expected/. They were created by
running main.py once on the sample briefs, and then checked by hand.
If a rule changes on purpose, create them again (see the README).
"""

import tempfile
import unittest
from pathlib import Path

from src.report import write_reports
from src.utils import load_brief
from src.validator import validate_brief
from src.validator_oop import validate_brief_oop
from tests.helpers import SAMPLE_DIR

EXPECTED_DIR = SAMPLE_DIR / "expected"
NAMES = [
    "valid_brief",
    "missing_section",
    "wrong_heading",
    "bad_type",
    "extra_fields",
]
IMPLEMENTATIONS = {
    "function": validate_brief,
    "oop": validate_brief_oop,
}


class TestExpectedReports(unittest.TestCase):
    """Compare freshly written reports with the saved ones."""

    def test_expected_files_exist(self) -> None:
        """Each sample brief has a saved CSV and JSON report."""
        for name in NAMES:
            for kind in ("csv", "json"):
                with self.subTest(file=name, kind=kind):
                    path = EXPECTED_DIR / f"{name}_report.{kind}"
                    self.assertTrue(path.is_file(), f"missing: {path}")

    def test_fresh_reports_match_the_saved_ones(self) -> None:
        """Both implementations reproduce the saved files exactly."""
        with tempfile.TemporaryDirectory() as folder:
            for name in NAMES:
                file_name = f"{name}.json"
                data = load_brief(SAMPLE_DIR / file_name)

                for label, validate in IMPLEMENTATIONS.items():
                    with self.subTest(file=name, implementation=label):
                        rows = validate(data, file_name)
                        _, csv_path, json_path = write_reports(
                            rows, Path(folder) / label, file_name
                        )
                        for fresh in (csv_path, json_path):
                            saved = EXPECTED_DIR / fresh.name
                            self.assertEqual(
                                fresh.read_text(encoding="utf-8"),
                                saved.read_text(encoding="utf-8"),
                            )
