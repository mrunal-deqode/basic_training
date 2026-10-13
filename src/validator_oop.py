"""Class-based validator for project briefs.

The same checks as validator.py, redesigned with classes:

* CheckResult       one check outcome (a PASS or a FAIL)
* ResultIterator    a hand-written iterator over results
* ComplianceReport  all the outcomes for one brief
* BaseChecker       parent of the three checkers below
    - HeadingChecker, FieldChecker, CoverageChecker
* BriefValidator    runs every checker and builds the report

validate_brief_oop() at the bottom has the same call shape as
validator.validate_brief(), so main.py can use either one.
"""

from pathlib import Path
from typing import Any, Iterator

from src.exceptions import InvalidDataTypeError, MissingSectionError
from src.report import build_summary
from src.utils import (
    BLUEPRINT_RULES,
    EXPECTED_HEADINGS,
    MODULE_TOPICS,
    check_brief_shape,
    load_brief,
    logged,
    timed,
)


class CheckResult:
    """The outcome of one check: a pass, or a failure of some severity.

    Class attributes:
        STATUSES: The allowed status values.
        SEVERITIES: The allowed severity values.
    """

    STATUSES = ("PASS", "FAIL")
    SEVERITIES = ("info", "warning", "error")

    def __init__(
        self,
        section: str,
        check: str,
        status: str,
        severity: str,
        message: str,
    ) -> None:
        """Store the five values after checking status and severity.

        Args:
            section: Where the check applies, e.g. "section 3".
            check: The kind of check, e.g. "heading".
            status: "PASS" or "FAIL".
            severity: "info", "warning" or "error".
            message: A human-readable explanation.

        Raises:
            ValueError: If status or severity is not an allowed value.
        """
        if status not in self.STATUSES:
            raise ValueError(
                f"status must be one of {self.STATUSES}, not {status!r}"
            )
        if severity not in self.SEVERITIES:
            raise ValueError(
                f"severity must be one of {self.SEVERITIES}, not {severity!r}"
            )
        self.section = section
        self.check = check
        self.status = status
        self.severity = severity
        self.message = message

    @classmethod
    def passed(cls, section: str, check: str, message: str) -> "CheckResult":
        """Create a passing result (its severity is always "info")."""
        return cls(section, check, "PASS", "info", message)

    @classmethod
    def failed(
        cls,
        section: str,
        check: str,
        message: str,
        severity: str = "error",
    ) -> "CheckResult":
        """Create a failing result (an error unless told otherwise)."""
        return cls(section, check, "FAIL", severity, message)

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> "CheckResult":
        """Create a result from a row dictionary (a 'file' key is ignored)."""
        return cls(
            row["section"],
            row["check"],
            row["status"],
            row["severity"],
            row["message"],
        )

    @property
    def is_violation(self) -> bool:
        """True if this check failed."""
        return self.status == "FAIL"

    def as_error(self) -> "CheckResult":
        """Return a copy of this result with the severity set to "error"."""
        return CheckResult(
            self.section, self.check, self.status, "error", self.message
        )

    def to_dict(self, file_name: str | None = None) -> dict[str, str]:
        """Return the result as a row dictionary.

        Args:
            file_name: If given, added to the row under the key "file".

        Returns:
            A dictionary with section, check, status, severity, message
            (and file).
        """
        row = {
            "section": self.section,
            "check": self.check,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
        }
        if file_name is not None:
            row["file"] = file_name
        return row

    def __eq__(self, other: object) -> bool:
        """Two results are equal when all five values are equal."""
        if not isinstance(other, CheckResult):
            return NotImplemented  # "I don't know how to compare with that"
        return self.to_dict() == other.to_dict()

    def __str__(self) -> str:
        """Return a short line for people to read."""
        return (
            f"[{self.status}] {self.section} / {self.check}: {self.message}"
        )

    def __repr__(self) -> str:
        """Return an unambiguous text, useful when debugging."""
        return (
            f"CheckResult(section={self.section!r}, check={self.check!r}, "
            f"status={self.status!r}, severity={self.severity!r}, "
            f"message={self.message!r})"
        )

class ResultIterator:
    """A hand-written iterator: it hands out results one at a time.

    An iterator needs two methods: __iter__ (returning itself) and
    __next__ (returning the next item, or raising StopIteration).
    """

    def __init__(self, results: list[CheckResult]) -> None:
        """Remember the results and start at the first one."""
        self._results = results
        self._index = 0

    def __iter__(self) -> "ResultIterator":
        """An iterator is its own iterator."""
        return self

    def __next__(self) -> CheckResult:
        """Return the next result, or stop when there are none left."""
        if self._index >= len(self._results):
            raise StopIteration
        result = self._results[self._index]
        self._index += 1
        return result


class ComplianceReport:
    """All the check results for one brief.

    A report can be looped over (it is iterable), measured with len(),
    and printed. Its score and verdict come from the shared report module.
    """

    def __init__(
        self,
        file_name: str = "brief",
        results: list[CheckResult] | None = None,
    ) -> None:
        """Create a report.

        Args:
            file_name: The brief file the results belong to.
            results: The results, or None for an empty report.
        """
        self.file_name = file_name
        # None as the default, then a fresh list. Never use [] as a default
        # value (Lesson 4), or every report would share one list.
        self.results = list(results) if results is not None else []

    def __len__(self) -> int:
        """Return how many results the report holds."""
        return len(self.results)

    def __iter__(self) -> ResultIterator:
        """Return a NEW iterator, so the report can be looped over often."""
        return ResultIterator(self.results)

    def violations(self, severity: str | None = None) -> Iterator[CheckResult]:
        """Yield the failed results one at a time (a generator).

        Args:
            severity: If given, yield only failures with this severity.

        Yields:
            Each matching failed CheckResult.
        """
        for result in self.results:
            if not result.is_violation:
                continue
            if severity is not None and result.severity != severity:
                continue
            yield result

    def to_rows(self) -> list[dict[str, str]]:
        """Return the results as row dictionaries, each with a 'file' key."""
        return [result.to_dict(self.file_name) for result in self.results]

    def summary(self) -> dict[str, Any]:
        """Return the summary dictionary (counts, score and verdict)."""
        return build_summary(self.to_rows(), self.file_name)

    @property
    def score(self) -> float:
        """The percentage of checks that passed."""
        return self.summary()["score"]

    @property
    def verdict(self) -> str:
        """The overall verdict, e.g. "COMPLIANT"."""
        return self.summary()["verdict"]

    def __str__(self) -> str:
        """Return a one-line description for people to read."""
        return f"{self.file_name}: {self.verdict} ({self.score}%)"

    def __repr__(self) -> str:
        """Return an unambiguous text, useful when debugging."""
        return (
            f"ComplianceReport(file_name={self.file_name!r}, "
            f"results={len(self.results)})"
        )

class BaseChecker:
    """Parent of all checkers: shared rules and helpers.

    Class attributes:
        name: A short name for the kind of checker.
        RULES: The blueprint rules (shared by every checker).
        HEADINGS: The expected headings, in order.
    """

    name = "base"
    RULES = BLUEPRINT_RULES
    HEADINGS = EXPECTED_HEADINGS

    def __init__(self, sections: list[Any]) -> None:
        """Remember the sections this checker will examine."""
        self.sections = sections

    @staticmethod
    def label(position: int) -> str:
        """Return the label for a 1-based section position."""
        return f"section {position}"

    def check(self) -> list[CheckResult]:
        """Run the checks. Every subclass must provide its own version."""
        raise NotImplementedError("Subclasses must implement check()")

    def __repr__(self) -> str:
        """Return an unambiguous text, e.g. HeadingChecker(sections=10)."""
        return f"{type(self).__name__}(sections={len(self.sections)})"


class HeadingChecker(BaseChecker):
    """Checks the section count and every heading."""

    name = "headings"

    def __init__(self, sections: list[Any]) -> None:
        """Set up the parent, then add a lower-case copy of the headings."""
        super().__init__(sections)
        self.lower_headings = [heading.lower() for heading in self.HEADINGS]

    @timed
    @logged
    def check(self) -> list[CheckResult]:
        """Run the section-count check and all heading checks."""
        results = [self.check_count()]
        results.extend(self.check_headings())
        return results

    def check_count(self) -> CheckResult:
        """Check that the brief has exactly the expected number of sections."""
        found = len(self.sections)
        expected = len(self.HEADINGS)

        if found == expected:
            return CheckResult.passed(
                "brief", "section count", f"Brief has exactly {found} sections"
            )
        return CheckResult.failed(
            "brief",
            "section count",
            f"Expected {expected} sections but found {found}",
        )

    def get_section(self, position: int) -> dict[str, Any]:
        """Return the section at a 1-based position.

        Raises:
            MissingSectionError: If the brief has fewer sections.
        """
        if position > len(self.sections):
            raise MissingSectionError(self.HEADINGS[position - 1])
        return self.sections[position - 1]

    @staticmethod
    def strip_number_prefix(text: str) -> str:
        """Remove a leading "2. " style number prefix, if there is one."""
        prefix, dot, rest = text.partition(". ")
        if dot and prefix.isdigit():
            return rest
        return text

    def check_one_heading(
        self, position: int, actual: str, expected: str
    ) -> CheckResult:
        """Compare one heading with the expected one and explain any gap."""
        label = self.label(position)

        if actual == expected:
            return CheckResult.passed(
                label, "heading", f"Heading is correct: '{expected}'"
            )

        cleaned = actual.strip()

        if cleaned == expected:
            message = f"Heading has extra spaces around it: '{actual}'"
        elif self.strip_number_prefix(cleaned) == expected:
            message = (f"Remove the number prefix: found '{actual}', "
                       f"expected '{expected}'")
        elif cleaned and cleaned[-1] == ":" and cleaned[:-1] == expected:
            message = (f"Remove the trailing colon: found '{actual}', "
                       f"expected '{expected}'")
        elif cleaned.lower() == expected.lower():
            message = (f"Wrong capital letters: found '{actual}', "
                       f"expected '{expected}'")
        elif cleaned.lower() in self.lower_headings:
            right_position = self.lower_headings.index(cleaned.lower()) + 1
            message = (f"Wrong order: '{cleaned}' belongs at position "
                       f"{right_position}, not {position}")
        else:
            message = (f"Heading does not match: found '{actual}', "
                       f"expected '{expected}'")

        return CheckResult.failed(label, "heading", message)

    def check_headings(self) -> list[CheckResult]:
        """Check every heading against the blueprint, in order."""
        results = []
        expected_count = len(self.HEADINGS)

        for position in range(1, expected_count + 1):
            expected = self.HEADINGS[position - 1]
            label = self.label(position)

            try:
                section = self.get_section(position)
            except MissingSectionError as error:
                results.append(
                    CheckResult.failed(label, "heading", str(error))
                )
            else:
                heading = section["heading"]
                results.append(
                    self.check_one_heading(position, heading, expected)
                )

        for position in range(expected_count + 1, len(self.sections) + 1):
            extra_heading = self.sections[position - 1]["heading"]
            results.append(
                CheckResult.failed(
                    self.label(position),
                    "heading",
                    f"Unexpected extra section: '{extra_heading}'",
                )
            )

        return results

class FieldChecker(BaseChecker):
    """Checks required fields, types, item counts, extras and blanks."""

    name = "fields"

    @timed
    @logged
    def check(self) -> list[CheckResult]:
        """Run every field check on every section that exists."""
        return list(self.iter_results())

    def iter_results(self) -> Iterator[CheckResult]:
        """Yield the field-check results one section at a time (a generator).

        Sections that are missing are skipped, because HeadingChecker
        already reports them.
        """
        for position in self.RULES:
            if position > len(self.sections):
                continue
            content = self.sections[position - 1]["content"]
            yield from self.check_section(position, content)

    def check_section(
        self, position: int, content: dict[str, Any]
    ) -> list[CheckResult]:
        """Run every field check for one section."""
        label = self.label(position)
        rules = self.RULES[position]["fields"]
        results = []

        for name, rule in rules.items():
            results.extend(self.check_field(label, name, rule, content))

        results.append(self.check_extra_fields(label, rules, content))
        results.append(self.check_blank_values(label, content))
        return results

    @staticmethod
    def ensure_type(field_name: str, value: Any, expected_type: type) -> None:
        """Raise an error if a value does not have the expected type.

        Raises:
            InvalidDataTypeError: If value is not an instance of
                expected_type.
        """
        if not isinstance(value, expected_type):
            raise InvalidDataTypeError(
                field_name, expected_type.__name__, value
            )

    def check_field(
        self,
        label: str,
        name: str,
        rule: dict[str, Any],
        content: dict[str, Any],
    ) -> list[CheckResult]:
        """Check one required field: presence, then type, then item count."""
        results = []

        if name not in content:
            results.append(
                CheckResult.failed(
                    label, "field", f"Missing required field '{name}'"
                )
            )
            return results
        results.append(
            CheckResult.passed(label, "field", f"Field '{name}' is present")
        )

        value = content[name]
        expected_type = rule["type"]
        try:
            self.ensure_type(name, value, expected_type)
        except InvalidDataTypeError as error:
            results.append(CheckResult.failed(label, "type", str(error)))
            return results
        results.append(
            CheckResult.passed(
                label,
                "type",
                f"Field '{name}' has type {expected_type.__name__}",
            )
        )

        if expected_type is list:
            results.append(self.check_item_count(label, name, value, rule))

        return results

    @staticmethod
    def check_item_count(
        label: str, name: str, items: list[Any], rule: dict[str, Any]
    ) -> CheckResult:
        """Check that a list field has an allowed number of items."""
        minimum = rule.get("min_items", 0)
        maximum = rule.get("max_items")
        count = len(items)

        if count < minimum:
            return CheckResult.failed(
                label,
                "item count",
                f"Field '{name}' needs at least {minimum} items "
                f"but has {count}",
            )
        if maximum is not None and count > maximum:
            return CheckResult.failed(
                label,
                "item count",
                f"Field '{name}' allows at most {maximum} items "
                f"but has {count}",
            )
        return CheckResult.passed(
            label, "item count", f"Field '{name}' has {count} items"
        )

    @staticmethod
    def check_extra_fields(
        label: str, rules: dict[str, Any], content: dict[str, Any]
    ) -> CheckResult:
        """Report fields that the blueprint does not ask for (a warning)."""
        # extra = set(content) - set(rules)
            # A set comprehension: names in content that the rules do not know.
        extra = {key for key in content if key not in rules}

        if extra:
            names = ", ".join(sorted(extra))
            return CheckResult.failed(
                label,
                "extra fields",
                f"Unexpected extra fields: {names}",
                severity="warning",
            )
        return CheckResult.passed(
            label, "extra fields", "No unexpected fields"
        )

    @classmethod
    def find_blank_values(cls, value: Any, path: str) -> list[str]:
        """Find blank values anywhere inside a nested structure (recursive).

        A value is blank if it is None, text holding only spaces, or an
        empty list or dictionary. This is a classmethod so that it can call
        itself through 'cls' without writing the class name.

        Returns:
            A list of paths that point to blank values.
        """
        blanks = []

        if isinstance(value, dict):
            if not value:
                return [path]
            for key, inner in value.items():
                blanks.extend(cls.find_blank_values(inner, f"{path}.{key}"))

        elif isinstance(value, list):
            if not value:
                return [path]
            for number, item in enumerate(value, start=1):
                blanks.extend(cls.find_blank_values(item, f"{path}[{number}]"))

        elif value is None:
            blanks.append(path)

        elif isinstance(value, str) and value.strip() == "":
            blanks.append(path)

        return blanks

    def check_blank_values(
        self, label: str, content: dict[str, Any]
    ) -> CheckResult:
        """Look for blank values anywhere inside a section's content."""
        blanks = []
        for key, value in content.items():
            blanks.extend(self.find_blank_values(value, key))

        if blanks:
            shown = ", ".join(blanks[:5])
            message = f"Blank values found at: {shown}"
            if len(blanks) > 5:
                message += f" (and {len(blanks) - 5} more)"
            return CheckResult.failed(label, "blank values", message)

        return CheckResult.passed(label, "blank values", "No blank values")

class CoverageChecker(BaseChecker):
    """Checks that every Module 1-5 topic is mentioned in the brief."""

    name = "coverage"

    def __init__(self, sections: list[Any]) -> None:
        """Set up the parent, then gather all the brief's text once."""
        super().__init__(sections)
        contents = [section["content"] for section in sections]
        # The function version kept this text inside a closure. Here it is
        # simply an attribute of the object.
        self.text = self.collect_text(contents).lower()

    @classmethod
    def collect_text(cls, value: Any) -> str:
        """Gather every text value inside a nested structure (recursive)."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            parts = [cls.collect_text(inner) for inner in value.values()]
            return " ".join(parts)
        if isinstance(value, list):
            parts = [cls.collect_text(item) for item in value]
            return " ".join(parts)
        return ""  # numbers, booleans and None hold no text

    def covers(self, keywords: list[str]) -> bool:
        """Return True if at least one keyword appears in the brief's text."""
        return any(keyword in self.text for keyword in keywords)

    @timed
    @logged
    def check(self) -> list[CheckResult]:
        """Check every topic of every module."""
        results = []

        for number, topics in MODULE_TOPICS.items():
            label = f"module {number}"
            for topic, keywords in topics.items():
                if self.covers(keywords):
                    results.append(
                        CheckResult.passed(
                            label, "topic coverage",
                            f"Topic '{topic}' is covered"
                        )
                    )
                else:
                    results.append(
                        CheckResult.failed(
                            label,
                            "topic coverage",
                            f"Topic '{topic}' is not mentioned anywhere "
                            "in the brief",
                        )
                    )

        return results


class BriefValidator:
    """Runs every checker on one brief and builds a ComplianceReport.

    Class attributes:
        CHECKER_CLASSES: The checkers to run, in order.
        KNOWN_OPTIONS: The option names validate() understands.
    """

    CHECKER_CLASSES = (HeadingChecker, FieldChecker, CoverageChecker)
    KNOWN_OPTIONS = {"skip_coverage"}

    def __init__(
        self,
        data: Any,
        file_name: str = "brief",
        strict: bool = False,
        **options: Any,
    ) -> None:
        """Check the brief's basic shape and remember the settings.

        Args:
            data: The parsed JSON brief (from load_brief).
            file_name: Name stamped on the report.
            strict: If True, warnings are treated as errors.
            **options: Optional switches. Supported: skip_coverage=True.

        Raises:
            InvalidDataTypeError: If the brief has the wrong basic types.
            MalformedRowError: If a required key is missing.
            TypeError: If an unknown option is given.
        """
        check_brief_shape(data)

        unknown = set(options) - self.KNOWN_OPTIONS
        if unknown:
            raise TypeError(f"Unknown options: {', '.join(sorted(unknown))}")

        self.data = data
        self.file_name = file_name
        self.strict = strict
        self.options = options

    @classmethod
    def from_file(
        cls, file_path: str | Path, strict: bool = False, **options: Any
    ) -> "BriefValidator":
        """Create a validator straight from a JSON file.

        Args:
            file_path: Path to the brief JSON file.
            strict: If True, warnings are treated as errors.
            **options: Passed on to the constructor.

        Raises:
            MissingFileError, EmptyInputError, MalformedRowError: From
                load_brief, if the file cannot be read.
        """
        data = load_brief(file_path)
        return cls(data, Path(file_path).name, strict, **options)

    def validate(self) -> ComplianceReport:
        """Run every checker and return the finished report."""
        sections = self.data["sections"]
        skip_coverage = self.options.get("skip_coverage", False)
        results = []

        for checker_class in self.CHECKER_CLASSES:
            if checker_class is CoverageChecker and skip_coverage:
                continue
            # Polymorphism: each class has its own check(), and this line
            # does not need to know which one it is calling.
            results.extend(checker_class(sections).check())

        if self.strict:
            results = [
                result.as_error() if result.severity == "warning" else result
                for result in results
            ]

        return ComplianceReport(self.file_name, results)


def validate_brief_oop(
    data: Any,
    file_name: str = "brief",
    strict: bool = False,
    **options: Any,
) -> list[dict[str, str]]:
    """Validate a brief with the class-based solution and return row dicts.

    This has the same arguments and the same return value as
    validator.validate_brief(), so main.py can use either one.

    Args:
        data: The parsed JSON brief (from load_brief).
        file_name: Name stamped on every row.
        strict: If True, warnings are treated as errors.
        **options: Optional switches. Supported: skip_coverage=True.

    Returns:
        Every result row, each with a 'file' key.
    """
    validator = BriefValidator(data, file_name, strict, **options)
    return validator.validate().to_rows()
