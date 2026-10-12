"""Function-based validator for project briefs."""
from functools import reduce
from typing import Any, Callable, Iterator

from src.exceptions import InvalidDataTypeError, MissingSectionError
from src.utils import (
    BLUEPRINT_RULES,
    EXPECTED_HEADINGS,
    MODULE_TOPICS,
    check_brief_shape,
    logged,
    timed,
)

EXPECTED_SECTION_COUNT = len(EXPECTED_HEADINGS)

LOWER_HEADINGS = [heading.lower() for heading in EXPECTED_HEADINGS]


HEADING_OK = 1 << 0  
FIELDS_OK = 1 << 1  
TYPES_OK = 1 << 2  
CONTENT_OK = 1 << 3  
ALL_OK = HEADING_OK | FIELDS_OK | TYPES_OK | CONTENT_OK  


CHECK_FLAGS = {
    "heading": HEADING_OK,
    "field": FIELDS_OK,
    "type": TYPES_OK,
    "item count": CONTENT_OK,
    "blank values": CONTENT_OK,
}

FLAG_NAMES = {
    HEADING_OK: "heading",
    FIELDS_OK: "fields",
    TYPES_OK: "types",
    CONTENT_OK: "content",
}


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

@timed
@logged
def validate_structure(sections: list[Any]) -> list[dict[str, str]]:
    """Validate the brief's section count and headings."""
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

def iter_field_results(sections: list[Any]) -> Iterator[dict[str, str]]:
    for position in BLUEPRINT_RULES:
        if position > len(sections):
            continue  
        content = sections[position - 1]["content"]
        yield from check_section_fields(position, content)


@timed
@logged
def validate_fields(sections: list[Any]) -> list[dict[str, str]]:
    return list(iter_field_results(sections))

def merge_results(
    *result_lists: list[dict[str, str]],
) -> list[dict[str, str]]:
    
    merged = []
    for result_list in result_lists:
        merged.extend(result_list)
    return merged


def collect_text(value: Any) -> str:
    
    if isinstance(value, str):  
        return value

    if isinstance(value, dict):  
        return " ".join(collect_text(inner) for inner in value.values())

    if isinstance(value, list):  
        return " ".join(collect_text(item) for item in value)

    return ""  


def make_keyword_finder(text: str) -> Callable[[list[str]], bool]:
    

    def found(keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    return found


def coverage_message(topic: str, found: bool) -> str:
    
    if found:
        return f"Topic '{topic}' is covered"
    return f"Topic '{topic}' is not mentioned anywhere in the brief"


@timed
@logged
def check_topic_coverage(sections: list[Any]) -> list[dict[str, str]]:
    
    contents = [section["content"] for section in sections]
    text = collect_text(contents).lower()  
    covers = make_keyword_finder(text)

    outcomes = [
        (number, topic, covers(keywords))
        for number, topics in MODULE_TOPICS.items()
        for topic, keywords in topics.items()
    ]

    return [
        make_result(f"module {number}", "topic coverage", found,
                    coverage_message(topic, found))
        for number, topic, found in outcomes
    ]


def get_failures(
    results: list[dict[str, str]], severity: str | None = None
) -> list[dict[str, str]]:
    failed = filter(lambda row: row["status"] == "FAIL", results)

    if severity is not None:
        failed = filter(lambda row: row["severity"] == severity, failed)

    return list(failed) 


def add_to_tally(tally: dict[str, int], row: dict[str, str]) -> dict[str, int]:
    tally[row["status"]] = tally[row["status"]] + 1
    return tally


def tally_results(results: list[dict[str, str]]) -> dict[str, int]:
    starting_tally = {"PASS": 0, "FAIL": 0}
    return reduce(add_to_tally, results, starting_tally)


def add_file_name(
    results: list[dict[str, str]], file_name: str
) -> list[dict[str, str]]:
    return list(map(lambda row: {**row, "file": file_name}, results))


def make_strict(results: list[dict[str, str]]) -> list[dict[str, str]]:
    strict_results = []
    for row in results:
        if row["severity"] == "warning":
            row = {**row, "severity": "error"}  
        strict_results.append(row)
    return strict_results


def section_status_masks(results: list[dict[str, str]]) -> dict[str, int]:
    masks = {}

    for row in results:
        label = row["section"]
        if not label.startswith("section "):
            continue  

        mask = masks.get(label, ALL_OK)  

        is_error = row["status"] == "FAIL" and row["severity"] == "error"
        if is_error:
            flag = CHECK_FLAGS.get(row["check"], 0)
            mask = mask & ~flag  

        masks[label] = mask

    return masks


def describe_mask(mask: int) -> list[str]:
    return [name for flag, name in FLAG_NAMES.items() if not (mask & flag)]


def validate_brief(
    data: Any,
    file_name: str = "brief",
    strict: bool = False,
    **options: Any,
) -> list[dict[str, str]]:
    check_brief_shape(data)  

    unknown = set(options) - {"skip_coverage"}
    if unknown:
        raise TypeError(f"Unknown options: {', '.join(sorted(unknown))}")

    sections = data["sections"]
    parts = [validate_structure(sections), validate_fields(sections)]

    if not options.get("skip_coverage", False):
        parts.append(check_topic_coverage(sections))

    results = merge_results(*parts)  

    if strict:
        results = make_strict(results)

    return add_file_name(results, file_name)

def iter_violations(
    results: list[dict[str, str]], severity: str | None = None
) -> Iterator[dict[str, str]]:
    for row in results:
        if row["status"] != "FAIL":
            continue
        if severity is not None and row["severity"] != severity:
            continue
        yield row