"""Report writing for the Blueprint Compliance Checker."""

import csv
import json
from pathlib import Path
from typing import Any

CSV_COLUMNS = ["file", "section", "check", "status", "severity", "message"]

ROW_TEMPLATE = "{section:<12} {check:<16} {severity:<8} {message}"
FILE_NAME_TEMPLATE = "{stem}_report.{extension}"


def count_results(results: list[dict[str, str]]) -> dict[str, int]:
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
    if total == 0:
        return 0.0
    return round(passed / total * 100, 1)


def get_verdict(total: int, errors: int) -> str:
    if total == 0:
        return "NOT CHECKED"
    if errors == 0:
        return "COMPLIANT"
    return "NON-COMPLIANT"


def build_summary(
    results: list[dict[str, str]], file_name: str = "brief"
) -> dict[str, Any]:
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
    stem = Path(file_name).stem  
    csv_name = FILE_NAME_TEMPLATE.format(stem=stem, extension="csv")
    json_name = FILE_NAME_TEMPLATE.format(stem=stem, extension="json")

    folder = Path(output_dir)
    return folder / csv_name, folder / json_name


def write_csv(
    results: list[dict[str, str]], csv_path: str | Path
) -> Path:
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
    path = Path(json_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {"summary": summary, "results": results}

    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")  

    return path


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"File    : {summary['file']}",
        (f"Checks  : {summary['total_checks']} total, "
         f"{summary['passed']} passed, {summary['failed']} failed"),
        f"Errors  : {summary['errors']}   Warnings: {summary['warnings']}",
        f"Score   : {summary['score']:.1f}%",
        f"Verdict : {summary['verdict']}",
    ]
    return "\n".join(lines)


def format_failure_table(results: list[dict[str, str]]) -> str:
    failed_rows = [row for row in results if row["status"] == "FAIL"]

    if not failed_rows:
        return "No failed checks."

    header = ROW_TEMPLATE.format(
        section="SECTION", check="CHECK", severity="SEVERITY",
        message="MESSAGE",
    )
    lines = [header, "-" * 70]

    for row in failed_rows:
        lines.append(ROW_TEMPLATE.format(**row))

    return "\n".join(lines)


def write_reports(
    results: list[dict[str, str]],
    output_dir: str | Path,
    file_name: str,
) -> tuple[dict[str, Any], Path, Path]:
    summary = build_summary(results, file_name)
    csv_path, json_path = make_output_paths(output_dir, file_name)

    write_csv(results, csv_path)
    write_json(summary, results, json_path)

    return summary, csv_path, json_path