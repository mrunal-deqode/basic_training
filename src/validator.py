"""Function-based validator for project briefs."""

from typing import Any

from src.exceptions import MissingSectionError
from src.utils import EXPECTED_HEADINGS

EXPECTED_SECTION_COUNT = len(EXPECTED_HEADINGS)

LOWER_HEADINGS = [heading.lower() for heading in EXPECTED_HEADINGS]


def make_result(
    section: str,
    check: str,
    passed: bool,
    message: str,
    severity: str = "error",
) -> dict[str, str]:
    
    if passed:
        status = "PASS"
        severity = "info"
    else:
        status = "FAIL"

    return {
        "section": section,
        "check": check,
        "status": status,
        "severity": severity,
        "message": message,
    }


def check_section_count(sections: list[Any]) -> list[dict[str, str]]:
    found = len(sections)

    if found == EXPECTED_SECTION_COUNT:
        message = f"Brief has exactly {found} sections"
        return [make_result("brief", "section count", True, message)]

    message = f"Expected {EXPECTED_SECTION_COUNT} sections but found {found}"
    return [make_result("brief", "section count", False, message)]


def get_section(sections: list[Any], position: int) -> dict[str, Any]:
    
    if position > len(sections):
        raise MissingSectionError(EXPECTED_HEADINGS[position - 1])

    return sections[position - 1]


def check_one_heading(position: int, actual: str, expected: str) -> dict[str, str]:
    
    label = f"section {position}"

    if actual == expected:
        return make_result(label, "heading", True,
                           f"Heading is correct: '{expected}'")

    cleaned = actual.strip()
    prefix, dot, rest = cleaned.partition(". ")

    if cleaned == expected:
        message = f"Heading has extra spaces around it: '{actual}'"
    elif dot and prefix.isdigit() and rest == expected:
        message = (f"Remove the number prefix: found '{actual}', "
                   f"expected '{expected}'")
    elif cleaned.lower() == expected.lower():
        message = (f"Wrong capital letters: found '{actual}', "
                   f"expected '{expected}'")
    elif cleaned.lower() in LOWER_HEADINGS:
        right_position = LOWER_HEADINGS.index(cleaned.lower()) + 1
        message = (f"Wrong order: '{cleaned}' belongs at position "
                   f"{right_position}, not {position}")
    else:
        message = (f"Heading does not match: found '{actual}', "
                   f"expected '{expected}'")

    return make_result(label, "heading", False, message)


def check_headings(sections: list[Any]) -> list[dict[str, str]]:
    
    results = []

    for position in range(1, EXPECTED_SECTION_COUNT + 1):
        expected = EXPECTED_HEADINGS[position - 1]

        try:
            section = get_section(sections, position)
        except MissingSectionError as error:
            results.append(
                make_result(f"section {position}", "heading", False, str(error))
            )
        else:
            results.append(check_one_heading(position, section["heading"], expected))

    for position in range(EXPECTED_SECTION_COUNT + 1, len(sections) + 1):
        extra_heading = sections[position - 1]["heading"]
        message = f"Unexpected extra section: '{extra_heading}'"
        results.append(make_result(f"section {position}", "heading", False, message))

    return results


def validate_structure(sections: list[Any]) -> list[dict[str, str]]:
    
    results = []
    results.extend(check_section_count(sections))
    results.extend(check_headings(sections))
    return results