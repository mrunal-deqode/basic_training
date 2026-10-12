"""Shared helpers for the test files."""

import json
from pathlib import Path
from typing import Any

# The project root is the folder above tests/. Building paths from
# __file__ means the tests work no matter where you run them from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "sample_data"


def load_sample(name: str) -> dict[str, Any]:
    """Load a sample brief from sample_data/ as a brand-new dictionary.

    Every call reads the file again, so each test gets its own copy and
    one test can never change the data another test sees.

    Args:
        name: The file name inside sample_data/, e.g. "valid_brief.json".

    Returns:
        The parsed JSON content.
    """
    with open(SAMPLE_DIR / name, encoding="utf-8") as file:
        return json.load(file)


def failures(
    results: list[dict[str, str]],
    check: str | None = None,
    section: str | None = None,
    severity: str | None = None,
) -> list[dict[str, str]]:
    """Pick the FAIL rows that match the given filters.

    Args:
        results: Result rows.
        check: If given, keep only rows with this check name.
        section: If given, keep only rows with this section label.
        severity: If given, keep only rows with this severity.

    Returns:
        The matching FAIL rows.
    """
    return [
        row
        for row in results
        if row["status"] == "FAIL"
        and (check is None or row["check"] == check)
        and (section is None or row["section"] == section)
        and (severity is None or row["severity"] == severity)
    ]