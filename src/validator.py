"""Function-based validator for project briefs."""

from typing import Any

from src.exceptions import InvalidDataTypeError, MissingSectionError
from src.utils import BLUEPRINT_RULES, EXPECTED_HEADINGS

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

def ensure_type(field_name: str, value: Any, expected_type: type) -> None:
    
    if not isinstance(value, expected_type):
        raise InvalidDataTypeError(field_name, expected_type.__name__, value)


def find_blank_values(value: Any, path: str) -> list[str]:
    
    blanks = []

    if isinstance(value, dict):
        if not value:  
            return [path]
        for key, inner in value.items():  
            blanks.extend(find_blank_values(inner, f"{path}.{key}"))

    elif isinstance(value, list):
        if not value:  
            return [path]
        for number, item in enumerate(value, start=1):
            blanks.extend(find_blank_values(item, f"{path}[{number}]"))

    elif value is None:  
        blanks.append(path)

    elif isinstance(value, str) and value.strip() == "":
        blanks.append(path)  
    return blanks


def check_item_count(
    label: str, name: str, items: list[Any], rule: dict[str, Any]
) -> dict[str, str]:
    minimum = rule.get("min_items", 0)  
    maximum = rule.get("max_items")  
    count = len(items)

    if count < minimum:
        message = (f"Field '{name}' needs at least {minimum} items "
                   f"but has {count}")
        return make_result(label, "item count", False, message)

    if maximum is not None and count > maximum:
        message = (f"Field '{name}' allows at most {maximum} items "
                   f"but has {count}")
        return make_result(label, "item count", False, message)

    message = f"Field '{name}' has {count} items"
    return make_result(label, "item count", True, message)


def check_field(
    label: str, name: str, rule: dict[str, Any], content: dict[str, Any]
) -> list[dict[str, str]]:
    
    results = []

    if name not in content:
        message = f"Missing required field '{name}'"
        results.append(make_result(label, "field", False, message))
        return results  
    results.append(
        make_result(label, "field", True, f"Field '{name}' is present")
    )

    value = content[name]
    expected_type = rule["type"]
    try:
        ensure_type(name, value, expected_type)
    except InvalidDataTypeError as error:
        results.append(make_result(label, "type", False, str(error)))
        return results  
    type_name = expected_type.__name__
    results.append(
        make_result(label, "type", True, f"Field '{name}' has type {type_name}")
    )

    
    if expected_type is list:
        results.append(check_item_count(label, name, value, rule))

    return results


def check_extra_fields(
    label: str, rules: dict[str, Any], content: dict[str, Any]
) -> dict[str, str]:
    extra = set(content) - set(rules)

    if extra:
        names = ", ".join(sorted(extra))  
        message = f"Unexpected extra fields: {names}"
        return make_result(label, "extra fields", False, message,
                           severity="warning")

    return make_result(label, "extra fields", True, "No unexpected fields")


def check_blank_values(label: str, content: dict[str, Any]) -> dict[str, str]:
    
    blanks = []
    for key, value in content.items():
        blanks.extend(find_blank_values(value, key))

    if blanks:
        shown = ", ".join(blanks[:5])  
        message = f"Blank values found at: {shown}"
        if len(blanks) > 5:
            message += f" (and {len(blanks) - 5} more)"
        return make_result(label, "blank values", False, message)

    return make_result(label, "blank values", True, "No blank values")


def check_section_fields(
    position: int, content: dict[str, Any]
) -> list[dict[str, str]]:
    
    label = f"section {position}"
    rules = BLUEPRINT_RULES[position]["fields"]
    results = []

    for name, rule in rules.items():
        results.extend(check_field(label, name, rule, content))

    results.append(check_extra_fields(label, rules, content))
    results.append(check_blank_values(label, content))
    return results


def validate_fields(sections: list[Any]) -> list[dict[str, str]]:
    
    results = []

    for position in BLUEPRINT_RULES:  
        if position > len(sections):
            continue  
        content = sections[position - 1]["content"]
        results.extend(check_section_fields(position, content))

    return results