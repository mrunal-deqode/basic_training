"""Function-based validator for project briefs.

This module checks a brief against the fixed 10-section blueprint using
plain functions. Every check returns a list of "result" dictionaries
with the keys: section, check, status, severity and message.
"""

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

# How many sections a correct brief must have.
EXPECTED_SECTION_COUNT = len(EXPECTED_HEADINGS)

# Each expected heading in lower case -> its 1-based position. Used to
# detect a heading that is correct but sitting in the wrong position.
HEADING_POSITIONS = {
    heading.lower(): number
    for number, heading in enumerate(EXPECTED_HEADINGS, start=1)
}

# Status flags: each one is a single bit, so they can be combined in one
# number. "1 << 3" means "shift the 1 three places left", which gives 8.
HEADING_OK = 1 << 0  # binary 0001 = 1
FIELDS_OK = 1 << 1  # binary 0010 = 2
TYPES_OK = 1 << 2  # binary 0100 = 4
CONTENT_OK = 1 << 3  # binary 1000 = 8
ALL_OK = HEADING_OK | FIELDS_OK | TYPES_OK | CONTENT_OK  # 1111 = 15

# Which flag each kind of check belongs to.
CHECK_FLAGS = {
    "heading": HEADING_OK,
    "field": FIELDS_OK,
    "type": TYPES_OK,
    "item count": CONTENT_OK,
    "blank values": CONTENT_OK,
}

# A readable name for each flag, used when describing a mask.
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
    """Build one result row.

    Args:
        section: Where the check applies, e.g. "brief" or "section 3".
        check: The kind of check, e.g. "heading".
        passed: True if the check passed, False if it failed.
        message: A human-readable explanation.
        severity: How serious a failure is. Ignored (set to "info") when
            the check passed.

    Returns:
        A dictionary with the keys section, check, status, severity, message.
    """
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
    """Check that the brief has exactly the expected number of sections.

    Args:
        sections: The list of section dictionaries from the brief.

    Returns:
        A list holding a single result row.
    """
    found = len(sections)

    if found == EXPECTED_SECTION_COUNT:
        message = f"Brief has exactly {found} sections"
        return [make_result("brief", "section count", True, message)]

    message = f"Expected {EXPECTED_SECTION_COUNT} sections but found {found}"
    return [make_result("brief", "section count", False, message)]


def get_section(sections: list[Any], position: int) -> dict[str, Any]:
    """Return the section at a 1-based position.

    Args:
        sections: The list of section dictionaries.
        position: Which section to fetch, counting from 1.

    Returns:
        The section dictionary.

    Raises:
        MissingSectionError: If the brief has fewer sections than position.
    """
    if position > len(sections):
        raise MissingSectionError(EXPECTED_HEADINGS[position - 1])

    return sections[position - 1]


def check_one_heading(
    position: int, actual: str, expected: str
) -> dict[str, str]:
    """Compare one heading with the expected one and explain any difference.

    Args:
        position: The 1-based position of the section.
        actual: The heading found in the brief.
        expected: The heading the blueprint requires at this position.

    Returns:
        A single result row.
    """
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
    elif cleaned and cleaned[-1] == ":" and cleaned[:-1] == expected:
        message = (f"Remove the trailing colon: found '{actual}', "
                   f"expected '{expected}'")
    elif cleaned.lower() == expected.lower():
        message = (f"Wrong capital letters: found '{actual}', "
                   f"expected '{expected}'")
    elif cleaned.lower() in HEADING_POSITIONS:
        right_position = HEADING_POSITIONS[cleaned.lower()]
        message = (f"Wrong order: '{cleaned}' belongs at position "
                   f"{right_position}, not {position}")
    else:
        message = (f"Heading does not match: found '{actual}', "
                   f"expected '{expected}'")

    return make_result(label, "heading", False, message)


def check_headings(sections: list[Any]) -> list[dict[str, str]]:
    """Check every heading against the blueprint, in order.

    Assumes check_brief_shape() already passed, so every section is a
    dictionary with a text 'heading'.

    Args:
        sections: The list of section dictionaries.

    Returns:
        One result row per expected position, plus one row for every
        unexpected extra section.
    """
    results = []

    for position in range(1, EXPECTED_SECTION_COUNT + 1):
        expected = EXPECTED_HEADINGS[position - 1]

        try:
            section = get_section(sections, position)
        except MissingSectionError as error:
            results.append(
                make_result(
                    f"section {position}", "heading", False, str(error)
                )
            )
        else:
            results.append(
                check_one_heading(position, section["heading"], expected)
            )

    for position in range(EXPECTED_SECTION_COUNT + 1, len(sections) + 1):
        extra_heading = sections[position - 1]["heading"]
        message = f"Unexpected extra section: '{extra_heading}'"
        results.append(
            make_result(f"section {position}", "heading", False, message)
        )

    return results


@timed
@logged
def validate_structure(sections: list[Any]) -> list[dict[str, str]]:
    """Validate the brief's section count and headings.

    Args:
        sections: The list of section dictionaries.

    Returns:
        All result rows from the structure checks, in order.
    """
    results = []
    results.extend(check_section_count(sections))
    results.extend(check_headings(sections))
    return results


def ensure_type(field_name: str, value: Any, expected_type: type) -> None:
    """Raise an error if a value does not have the expected type.

    Args:
        field_name: Name of the field, used in the error message.
        value: The value to check.
        expected_type: The type the blueprint requires, e.g. str or list.

    Raises:
        InvalidDataTypeError: If value is not an instance of expected_type.
    """
    if not isinstance(value, expected_type):
        raise InvalidDataTypeError(field_name, expected_type.__name__, value)


def find_blank_values(value: Any, path: str) -> list[str]:
    """Find blank values anywhere inside a nested structure (recursive).

    A value is blank if it is None, a string holding only spaces, or an
    empty list or dictionary.

    Args:
        value: The value to inspect: a dict, a list or a simple value.
        path: A readable name for where the value sits, e.g. "fields.name".

    Returns:
        A list of paths that point to blank values (empty if none).
    """
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
    """Check that a list field has an allowed number of items.

    Args:
        label: Where the field lives, e.g. "section 9".
        name: The field name.
        items: The list stored in the field.
        rule: The field's rule, which may hold min_items and max_items.

    Returns:
        A single result row.
    """
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
    """Check one required field: presence, then type, then item count.

    Args:
        label: Where the field lives, e.g. "section 4".
        name: The required field name.
        rule: The rule for this field (its type and optional limits).
        content: The section's content dictionary.

    Returns:
        One to three result rows, depending on how far the checks get.
    """
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
        make_result(
            label, "type", True, f"Field '{name}' has type {type_name}"
        )
    )

    if expected_type is list:
        results.append(check_item_count(label, name, value, rule))

    return results


def check_extra_fields(
    label: str, rules: dict[str, Any], content: dict[str, Any]
) -> dict[str, str]:
    """Report fields that the blueprint does not ask for (a warning).

    Args:
        label: Where the content lives, e.g. "section 2".
        rules: The field rules for this section.
        content: The section's content dictionary.

    Returns:
        A single result row.
    """
    extra = set(content) - set(rules)

    if extra:
        names = ", ".join(sorted(extra))
        message = f"Unexpected extra fields: {names}"
        return make_result(label, "extra fields", False, message,
                           severity="warning")

    return make_result(label, "extra fields", True, "No unexpected fields")


def check_blank_values(label: str, content: dict[str, Any]) -> dict[str, str]:
    """Look for blank values anywhere inside a section's content.

    Args:
        label: Where the content lives, e.g. "section 5".
        content: The section's content dictionary.

    Returns:
        A single result row.
    """
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
    """Run every field check for one section.

    Args:
        position: The 1-based section number (selects the rules).
        content: The section's content dictionary.

    Returns:
        All result rows for this section.
    """
    label = f"section {position}"
    rules = BLUEPRINT_RULES[position]["fields"]
    results = []

    for name, rule in rules.items():
        results.extend(check_field(label, name, rule, content))

    results.append(check_extra_fields(label, rules, content))
    results.append(check_blank_values(label, content))
    return results


def iter_field_results(sections: list[Any]) -> Iterator[dict[str, str]]:
    """Yield the field-check rows, one section at a time (a generator).

    Calling this function does not run any checks. The checks for a
    section run only when the next row is requested, so a caller that
    stops early never pays for the sections it did not reach.

    Sections that are missing are skipped, because validate_structure()
    already reports them.

    Args:
        sections: The list of section dictionaries.

    Yields:
        Result rows, section by section.
    """
    for position in BLUEPRINT_RULES:
        if position > len(sections):
            continue
        content = sections[position - 1]["content"]
        yield from check_section_fields(position, content)


@timed
@logged
def validate_fields(sections: list[Any]) -> list[dict[str, str]]:
    """Check the fields of every section that exists.

    Args:
        sections: The list of section dictionaries.

    Returns:
        All field-related result rows, section by section.
    """
    return list(iter_field_results(sections))


def merge_results(
    *result_lists: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Join any number of result lists into one list.

    Args:
        *result_lists: One or more lists of result rows.

    Returns:
        A single list holding every row, in the order given.
    """
    merged = []
    for result_list in result_lists:
        merged.extend(result_list)
    return merged


def collect_text(value: Any) -> str:
    """Gather every text value inside a nested structure (recursive).

    Args:
        value: A string, a dict, a list, or any other value.

    Returns:
        All the text found, joined with spaces. Numbers, booleans and
        None contribute nothing.
    """
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return " ".join(collect_text(inner) for inner in value.values())

    if isinstance(value, list):
        return " ".join(collect_text(item) for item in value)

    return ""


def make_keyword_finder(text: str) -> Callable[[list[str]], bool]:
    """Create a function that searches a fixed text for keywords.

    This is a closure: the inner function remembers 'text' even after
    make_keyword_finder has finished running.

    Args:
        text: The (lower-case) text to search in.

    Returns:
        A function that takes a list of keywords and returns True if at
        least one of them appears in the text.
    """

    def found(keywords: list[str]) -> bool:
        """Return True if any keyword appears in the remembered text."""
        return any(keyword in text for keyword in keywords)

    return found


def coverage_message(topic: str, found: bool) -> str:
    """Build the message for one curriculum topic.

    Args:
        topic: The topic name.
        found: Whether the topic was found in the brief.

    Returns:
        A short human-readable message.
    """
    if found:
        return f"Topic '{topic}' is covered"
    return f"Topic '{topic}' is not mentioned anywhere in the brief"


@timed
@logged
def check_topic_coverage(sections: list[Any]) -> list[dict[str, str]]:
    """Check that every Module 1-5 topic is mentioned in the brief.

    Args:
        sections: The list of section dictionaries.

    Returns:
        One result row per topic, labelled with its module number.
    """
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
    """Pick out the failed rows, optionally of one severity only.

    Args:
        results: Result rows.
        severity: If given, keep only failures with this severity.

    Returns:
        A list of the matching FAIL rows.
    """
    failed = filter(lambda row: row["status"] == "FAIL", results)

    if severity is not None:
        failed = filter(lambda row: row["severity"] == severity, failed)

    return list(failed)


def add_to_tally(tally: dict[str, int], row: dict[str, str]) -> dict[str, int]:
    """Add one result row to a running PASS/FAIL tally (used by reduce).

    Args:
        tally: The counts so far, e.g. {"PASS": 5, "FAIL": 1}.
        row: The next result row.

    Returns:
        The updated tally.
    """
    tally[row["status"]] = tally[row["status"]] + 1
    return tally


def tally_results(results: list[dict[str, str]]) -> dict[str, int]:
    """Count how many rows passed and how many failed.

    Args:
        results: Result rows.

    Returns:
        A dictionary such as {"PASS": 100, "FAIL": 6}.
    """
    # Created INSIDE the function, so every call starts from zero.
    starting_tally = {"PASS": 0, "FAIL": 0}
    return reduce(add_to_tally, results, starting_tally)


def add_file_name(
    results: list[dict[str, str]], file_name: str
) -> list[dict[str, str]]:
    """Return copies of the rows with a 'file' key added.

    Args:
        results: Result rows.
        file_name: The brief file these rows belong to.

    Returns:
        New rows. The originals are not modified.
    """
    return list(map(lambda row: {**row, "file": file_name}, results))


def make_strict(results: list[dict[str, str]]) -> list[dict[str, str]]:
    """Turn every warning into an error (used in strict mode).

    Args:
        results: Result rows.

    Returns:
        New list in which no row has severity "warning".
    """
    strict_results = []
    for row in results:
        if row["severity"] == "warning":
            row = {**row, "severity": "error"}
        strict_results.append(row)
    return strict_results


def section_status_masks(results: list[dict[str, str]]) -> dict[str, int]:
    """Summarise each section as a bitmask of what passed.

    Every section starts with all bits on (ALL_OK). Each failed error
    switches off the bit that belongs to that kind of check. Warnings and
    passes change nothing.

    Args:
        results: Result rows.

    Returns:
        A dictionary such as {"section 1": 15, "section 3": 14}.
    """
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
    """Name the areas whose bits are switched off in a status mask.

    Args:
        mask: A status bitmask.

    Returns:
        A list of area names, e.g. ["fields", "types"]. Empty if all OK.
    """
    return [name for flag, name in FLAG_NAMES.items() if not (mask & flag)]


def validate_brief(
    data: Any,
    file_name: str = "brief",
    strict: bool = False,
    **options: Any,
) -> list[dict[str, str]]:
    """Run every check on a loaded brief and return all result rows.

    Args:
        data: The parsed JSON brief (from load_brief).
        file_name: Name stamped on every row, to say where it came from.
        strict: If True, warnings are treated as errors.
        **options: Optional switches. Supported: skip_coverage=True.

    Returns:
        Every result row, each with a 'file' key.

    Raises:
        InvalidDataTypeError: If the brief has the wrong basic types.
        MalformedRowError: If a required key is missing.
        TypeError: If an unknown option is given.
    """
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
    """Yield the failed rows one at a time (a generator).

    Unlike get_failures(), which builds a whole list immediately, this
    hands out one row per request.

    Args:
        results: Result rows.
        severity: If given, yield only failures with this severity.

    Yields:
        Each matching FAIL row.
    """
    for row in results:
        if row["status"] != "FAIL":
            continue
        if severity is not None and row["severity"] != severity:
            continue
        yield row
