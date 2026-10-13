"""Report writing for the Blueprint Compliance Checker.

This module turns a list of result rows into a summary, a CSV file, a
JSON file and printable text. It only works with plain dictionaries, so
both the function-based and the class-based validator can use it.
"""

import csv
import json
from pathlib import Path
from typing import Any, Iterator

CSV_COLUMNS = ["file", "section", "check", "status", "severity", "message"]

ROW_TEMPLATE = "{section:<12} {check:<16} {severity:<8} {message}"
FILE_NAME_TEMPLATE = "{stem}_report.{extension}"


def count_results(results: list[dict[str, str]]) -> dict[str, int]:
    """Count the result rows by status and severity.

    Args:
        results: Result rows, each with 'status' and 'severity' keys.

    Returns:
        A dictionary with the counts: total, passed, failed, errors and
        warnings. A failed row counts as an error unless its severity is
        "warning".
    """
    counts = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "warnings": 0,
    }

    for row in results:
        counts["total"] += 1
        if row["status"] == "PASS":
            counts["passed"] += 1
        else:
            counts["failed"] += 1
            if row["severity"] == "warning":
                counts["warnings"] += 1
            else:
                counts["errors"] += 1

    return counts


def calculate_score(passed: int, total: int) -> float:
    """Return the percentage of checks that passed.

    Args:
        passed: Number of passed checks.
        total: Total number of checks.

    Returns:
        The score from 0.0 to 100.0, rounded to one decimal place.
        Returns 0.0 when there were no checks, to avoid dividing by zero.
    """
    if total == 0:
        return 0.0
    return round(passed / total * 100, 1)


def get_verdict(total: int, errors: int) -> str:
    """Decide the overall verdict.

    Args:
        total: Total number of checks that ran.
        errors: Number of failed checks with severity "error".

    Returns:
        "NOT CHECKED", "COMPLIANT" or "NON-COMPLIANT".
    """
    if total == 0:
        return "NOT CHECKED"
    if errors == 0:
        return "COMPLIANT"
    return "NON-COMPLIANT"


def build_summary(
    results: list[dict[str, str]], file_name: str = "brief"
) -> dict[str, Any]:
    """Build the summary of one compliance run.

    Args:
        results: Result rows.
        file_name: Name of the brief file that was checked.

    Returns:
        A dictionary with file, total_checks, passed, failed, errors,
        warnings, score and verdict.
    """
    counts = count_results(results)

    return {
        "file": file_name,
        "total_checks": counts["total"],
        "passed": counts["passed"],
        "failed": counts["failed"],
        "errors": counts["errors"],
        "warnings": counts["warnings"],
        "score": calculate_score(counts["passed"], counts["total"]),
        "verdict": get_verdict(counts["total"], counts["errors"]),
    }


def make_output_paths(
    output_dir: str | Path, file_name: str
) -> tuple[Path, Path]:
    """Work out the CSV and JSON report paths for a brief.

    Args:
        output_dir: The folder the reports will be written to.
        file_name: The brief's file name, e.g. "valid_brief.json".

    Returns:
        A tuple (csv_path, json_path), e.g. (Path("out/a_report.csv"),
        Path("out/a_report.json")).
    """
    stem = Path(file_name).stem
    csv_name = FILE_NAME_TEMPLATE.format(stem=stem, extension="csv")
    json_name = FILE_NAME_TEMPLATE.format(stem=stem, extension="json")

    folder = Path(output_dir)
    return folder / csv_name, folder / json_name


def write_csv(
    results: list[dict[str, str]], csv_path: str | Path
) -> Path:
    """Write the result rows to a CSV file.

    Args:
        results: Result rows.
        csv_path: Where to write the file. Missing folders are created.

    Returns:
        The path that was written.
    """
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=CSV_COLUMNS, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(results)

    return path


def write_json(
    summary: dict[str, Any],
    results: list[dict[str, str]],
    json_path: str | Path,
) -> Path:
    """Write the summary and all result rows to a JSON file.

    Args:
        summary: The dictionary from build_summary().
        results: Result rows.
        json_path: Where to write the file. Missing folders are created.

    Returns:
        The path that was written.
    """
    path = Path(json_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {"summary": summary, "results": results}

    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")

    return path


def format_summary(summary: dict[str, Any]) -> str:
    """Format a summary as a few lines of text for the screen.

    Args:
        summary: The dictionary from build_summary().

    Returns:
        A multi-line string.
    """
    lines = [
        f"File    : {summary['file']}",
        (f"Checks  : {summary['total_checks']} total, "
         f"{summary['passed']} passed, {summary['failed']} failed"),
        f"Errors  : {summary['errors']}   Warnings: {summary['warnings']}",
        f"Score   : {summary['score']:.1f}%",
        f"Verdict : {summary['verdict']}",
    ]
    return "\n".join(lines)


def iter_failure_lines(results: list[dict[str, str]]) -> Iterator[str]:
    """Yield the failure table one line at a time (a generator).

    Makes one pass over the rows. The header is yielded just before the
    first failure, and if there is no failure at all, a short message is
    yielded instead.

    Args:
        results: Result rows.

    Yields:
        The lines of the table.
    """
    header_shown = False

    for row in results:
        if row["status"] != "FAIL":
            continue

        if not header_shown:
            yield ROW_TEMPLATE.format(
                section="SECTION", check="CHECK", severity="SEVERITY",
                message="MESSAGE",
            )
            yield "-" * 70
            header_shown = True

        yield ROW_TEMPLATE.format(**row)

    if not header_shown:
        yield "No failed checks."


def format_failure_table(results: list[dict[str, str]]) -> str:
    """Format the failed rows as an aligned text table.

    Args:
        results: Result rows.

    Returns:
        A multi-line string, or a short message if nothing failed.
    """
    return "\n".join(iter_failure_lines(results))


def write_reports(
    results: list[dict[str, str]],
    output_dir: str | Path,
    file_name: str,
) -> tuple[dict[str, Any], Path, Path]:
    """Build the summary and write both report files.

    Args:
        results: Result rows.
        output_dir: The folder the reports will be written to.
        file_name: The brief's file name (used for the summary and for
            naming the report files).

    Returns:
        A tuple (summary, csv_path, json_path).
    """
    summary = build_summary(results, file_name)
    csv_path, json_path = make_output_paths(output_dir, file_name)

    write_csv(results, csv_path)
    write_json(summary, results, json_path)

    return summary, csv_path, json_path
