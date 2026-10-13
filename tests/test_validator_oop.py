"""Unit tests for the class-based validator (src/validator_oop.py).

These tests focus on what is specific to the class design: result
objects, dunder methods, the iterator, inheritance, class methods and
static methods. That both implementations give the same rows for many
broken briefs is checked separately in tests/test_parity.py.

Run all tests from the project root with:
    python -m unittest discover -v
"""

import tempfile
import types
import unittest
from itertools import islice
from pathlib import Path
from typing import Any

from src.exceptions import (
    EmptyInputError,
    InvalidDataTypeError,
    MalformedRowError,
    MissingFileError,
    MissingSectionError,
)
from src.utils import BLUEPRINT_RULES, TIMINGS
from src.validator_oop import (
    BaseChecker,
    BriefValidator,
    CheckResult,
    ComplianceReport,
    CoverageChecker,
    FieldChecker,
    HeadingChecker,
    ResultIterator,
    validate_brief_oop,
)
from tests.helpers import SAMPLE_DIR, load_sample


def run(brief: dict[str, Any], **options: Any) -> ComplianceReport:
    """Validate a brief as 'test.json' and return the report.

    Args:
        brief: The brief dictionary to validate.
        **options: Passed on to BriefValidator (strict, skip_coverage).

    Returns:
        The finished ComplianceReport.
    """
    return BriefValidator(brief, "test.json", **options).validate()


def failed(
    results: list[CheckResult],
    check: str | None = None,
    section: str | None = None,
) -> list[CheckResult]:
    """Pick the failed results that match the given filters.

    Args:
        results: A list of CheckResult objects.
        check: If given, keep only results with this check name.
        section: If given, keep only results with this section label.

    Returns:
        The matching failed results.
    """
    return [
        result
        for result in results
        if result.is_violation
        and (check is None or result.check == check)
        and (section is None or result.section == section)
    ]


def sample_results() -> list[CheckResult]:
    """Build four small results: two passes, one error and one warning."""
    return [
        CheckResult.passed("section 1", "heading", "ok"),
        CheckResult.passed("section 2", "heading", "ok"),
        CheckResult.failed("section 3", "heading", "bad"),
        CheckResult.failed(
            "section 4", "extra fields", "hmm", severity="warning"
        ),
    ]

class TestCheckResult(unittest.TestCase):
    """The result object, its factories and its special methods."""

    def test_passed_factory(self) -> None:
        """A passed result always has the severity 'info'."""
        result = CheckResult.passed("section 1", "heading", "ok")

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.severity, "info")
        self.assertFalse(result.is_violation)

    def test_failed_factory(self) -> None:
        """A failed result is an error unless told otherwise."""
        error = CheckResult.failed("section 1", "heading", "bad")
        warning = CheckResult.failed(
            "section 1", "extra fields", "hmm", severity="warning"
        )

        self.assertEqual(error.severity, "error")
        self.assertTrue(error.is_violation)
        self.assertEqual(warning.severity, "warning")

    def test_invalid_values_are_rejected(self) -> None:
        """__init__ refuses a status or severity it does not know."""
        with self.assertRaises(ValueError):
            CheckResult("s", "c", "MAYBE", "error", "m")
        with self.assertRaises(ValueError):
            CheckResult("s", "c", "FAIL", "urgent", "m")

    def test_equality(self) -> None:
        """Results with the same five values are equal."""
        first = CheckResult.failed("section 3", "heading", "Bad heading")
        same = CheckResult("section 3", "heading", "FAIL", "error",
                           "Bad heading")
        other = CheckResult.failed("section 3", "heading", "Another message")

        self.assertEqual(first, same)
        self.assertNotEqual(first, other)
        self.assertNotEqual(first, "text")  # a different type: not equal
        self.assertNotEqual(first, first.to_dict())

    def test_str_and_repr(self) -> None:
        """str() is for people and repr() is for debugging."""
        result = CheckResult.failed("section 3", "heading", "Bad heading")

        self.assertEqual(
            str(result), "[FAIL] section 3 / heading: Bad heading"
        )
        self.assertTrue(
            repr(result).startswith("CheckResult(section='section 3'")
        )

    def test_repr_can_recreate_the_object(self) -> None:
        """repr() looks like code, so running it builds an equal object."""
        result = CheckResult.failed("section 3", "heading", "Bad heading")
        self.assertEqual(eval(repr(result)), result)

    def test_to_dict(self) -> None:
        """to_dict gives five keys, or six when a file name is given."""
        result = CheckResult.failed("section 3", "heading", "Bad heading")

        self.assertEqual(
            result.to_dict(),
            {
                "section": "section 3",
                "check": "heading",
                "status": "FAIL",
                "severity": "error",
                "message": "Bad heading",
            },
        )
        self.assertEqual(result.to_dict("a.json")["file"], "a.json")

    def test_from_dict_ignores_the_file_key(self) -> None:
        """A result survives a trip through a row dictionary."""
        result = CheckResult.failed("section 3", "heading", "Bad heading")
        row = result.to_dict("a.json")

        self.assertEqual(CheckResult.from_dict(row), result)

    def test_as_error_returns_a_new_object(self) -> None:
        """Promoting a warning leaves the original unchanged."""
        warning = CheckResult.failed(
            "section 1", "extra fields", "hmm", severity="warning"
        )
        promoted = warning.as_error()

        self.assertEqual(promoted.severity, "error")
        self.assertEqual(warning.severity, "warning")
        self.assertIsNot(promoted, warning)

    def test_results_are_unhashable(self) -> None:
        """Defining __eq__ without __hash__ makes objects unhashable."""
        result = CheckResult.passed("section 1", "heading", "ok")
        with self.assertRaises(TypeError):
            hash(result)

    def test_factories_build_the_subclass(self) -> None:
        """Classmethods use 'cls', so a subclass gets its own type back."""

        class FancyResult(CheckResult):
            """A subclass defined only for this test."""

        self.assertIsInstance(FancyResult.passed("s", "c", "m"), FancyResult)
        self.assertIsInstance(FancyResult.failed("s", "c", "m"), FancyResult)


class TestIteratorAndReport(unittest.TestCase):
    """The hand-written iterator and the ComplianceReport."""

    def test_iterator_protocol(self) -> None:
        """__iter__ returns itself and __next__ ends with StopIteration."""
        results = sample_results()[:2]
        iterator = ResultIterator(results)

        self.assertIs(iter(iterator), iterator)
        self.assertEqual(next(iterator), results[0])
        self.assertEqual(next(iterator), results[1])
        with self.assertRaises(StopIteration):
            next(iterator)

    def test_report_can_be_looped_over_repeatedly(self) -> None:
        """Each loop gets a NEW iterator, so a report is not used up."""
        report = ComplianceReport("demo.json", sample_results())

        self.assertEqual(list(report), sample_results())
        self.assertEqual(list(report), sample_results())
        self.assertIsInstance(iter(report), ResultIterator)
        self.assertIsNot(iter(report), iter(report))

    def test_len_and_truthiness(self) -> None:
        """An empty report is falsy, like an empty list."""
        empty = ComplianceReport("demo.json")
        full = ComplianceReport("demo.json", sample_results())

        self.assertEqual(len(empty), 0)
        self.assertFalse(empty)
        self.assertEqual(len(full), 4)
        self.assertTrue(full)

    def test_default_results_are_not_shared(self) -> None:
        """Two reports built without results have separate lists."""
        first = ComplianceReport("a.json")
        second = ComplianceReport("b.json")
        first.results.append(CheckResult.passed("brief", "x", "ok"))

        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 0)

    def test_constructor_copies_the_list(self) -> None:
        """Changing the caller's list later does not change the report."""
        original = sample_results()
        report = ComplianceReport("a.json", original)
        original.clear()

        self.assertEqual(len(report), 4)

    def test_violations_is_a_generator(self) -> None:
        """violations() is lazy and can be consumed only once."""
        report = ComplianceReport("a.json", sample_results())
        violations = report.violations()

        self.assertIsInstance(violations, types.GeneratorType)
        self.assertEqual(len(list(violations)), 2)
        self.assertEqual(list(violations), [])

    def test_violations_severity_filter(self) -> None:
        """Failures can be filtered by severity."""
        report = ComplianceReport("a.json", sample_results())

        errors = list(report.violations("error"))
        warnings = list(report.violations("warning"))

        self.assertEqual([r.section for r in errors], ["section 3"])
        self.assertEqual([r.section for r in warnings], ["section 4"])

    def test_summary_score_and_verdict(self) -> None:
        """Counts, score and verdict come from the shared report module."""
        report = ComplianceReport("demo.json", sample_results())
        summary = report.summary()

        self.assertEqual(summary["total_checks"], 4)
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["warnings"], 1)
        self.assertEqual(report.score, 50.0)
        self.assertEqual(report.verdict, "NON-COMPLIANT")

        warning_only = ComplianceReport(
            "demo.json", [sample_results()[0], sample_results()[3]]
        )
        self.assertEqual(warning_only.verdict, "COMPLIANT")

    def test_empty_report(self) -> None:
        """A report with no results is 'NOT CHECKED', with score 0.0."""
        report = ComplianceReport("empty.json")

        self.assertEqual(report.score, 0.0)
        self.assertEqual(report.verdict, "NOT CHECKED")

    def test_to_rows_stamps_the_file_name(self) -> None:
        """Every row dictionary carries the report's file name."""
        report = ComplianceReport("demo.json", sample_results())
        rows = report.to_rows()

        self.assertEqual(len(rows), 4)
        self.assertEqual({row["file"] for row in rows}, {"demo.json"})
        self.assertEqual(rows[0]["section"], "section 1")

    def test_str_and_repr(self) -> None:
        """The report describes itself in one line."""
        report = ComplianceReport("demo.json", sample_results())

        self.assertEqual(str(report), "demo.json: NON-COMPLIANT (50.0%)")
        self.assertEqual(
            repr(report), "ComplianceReport(file_name='demo.json', results=4)"
        )

class TestInheritanceAndHelpers(unittest.TestCase):
    """BaseChecker, super(), class attributes, static and class methods."""

    def test_base_checker_check_must_be_overridden(self) -> None:
        """The parent only promises check(); it does not implement it."""
        with self.assertRaises(NotImplementedError):
            BaseChecker([]).check()

    def test_every_checker_is_a_base_checker(self) -> None:
        """All three checkers inherit from BaseChecker."""
        classes = (HeadingChecker, FieldChecker, CoverageChecker)

        for checker_class in classes:
            self.assertTrue(issubclass(checker_class, BaseChecker))
        names = {checker_class.name for checker_class in classes}
        self.assertEqual(names, {"headings", "fields", "coverage"})

    def test_class_attributes_are_shared(self) -> None:
        """The rules exist once, on the parent, and children inherit them."""
        self.assertIs(BaseChecker.RULES, BLUEPRINT_RULES)
        self.assertIs(HeadingChecker.RULES, BaseChecker.RULES)
        self.assertIs(FieldChecker.RULES, BaseChecker.RULES)

    def test_label_is_a_static_method(self) -> None:
        """label() works on the class and on an instance."""
        self.assertEqual(BaseChecker.label(3), "section 3")
        self.assertEqual(HeadingChecker([]).label(3), "section 3")

    def test_checker_repr(self) -> None:
        """A checker's repr names its class and the sections it holds."""
        self.assertEqual(
            repr(HeadingChecker([])), "HeadingChecker(sections=0)")
        self.assertEqual(
            repr(FieldChecker([1, 2])), "FieldChecker(sections=2)"
        )

    def test_heading_checker_calls_super_init(self) -> None:
        """The parent stores the sections, the child adds its own data."""
        sections = load_sample("valid_brief.json")["sections"]
        checker = HeadingChecker(sections)

        self.assertIs(checker.sections, sections)  # set by BaseChecker
        self.assertEqual(len(checker.lower_headings), 10)  # set by the child
        self.assertEqual(checker.lower_headings[0], "business scenario")

    def test_strip_number_prefix(self) -> None:
        """Only a real 'number, dot, space' prefix is removed."""
        strip = HeadingChecker.strip_number_prefix
        unchanged = [
            "Input Specification",
            "x. Input Specification",
            "2.Input Specification",
        ]

        self.assertEqual(
            strip("2. Input Specification"), "Input Specification"
        )
        for text in unchanged:
            with self.subTest(text=text):
                self.assertEqual(strip(text), text)

    def test_ensure_type(self) -> None:
        """A matching type passes silently and a wrong one raises."""
        self.assertIsNone(FieldChecker.ensure_type("count", 5, int))

        with self.assertRaises(InvalidDataTypeError) as context:
            FieldChecker.ensure_type("count", "5", int)
        self.assertEqual(context.exception.expected, "int")
        self.assertEqual(context.exception.actual, "str")

    def test_check_item_count_boundaries(self) -> None:
        """The limits are inclusive, and a missing limit means no limit."""
        rule = {"type": list, "min_items": 2, "max_items": 3}

        for count, status in ((1, "FAIL"), (2, "PASS"), (3, "PASS"),
                              (4, "FAIL")):
            with self.subTest(count=count):
                result = FieldChecker.check_item_count(
                    "section 9", "goals", ["x"] * count, rule
                )
                self.assertEqual(result.status, status)

        no_limits = FieldChecker.check_item_count(
            "section 9", "goals", [], {"type": list}
        )
        self.assertEqual(no_limits.status, "PASS")

    def test_find_blank_values(self) -> None:
        """The recursive classmethod finds blanks at every depth."""
        sample = {
            "a": "ok",
            "b": {"c": "", "d": ["x", None, {"e": " "}]},
            "f": [],
        }
        self.assertEqual(
            FieldChecker.find_blank_values(sample, "root"),
            ["root.b.c", "root.b.d[2]", "root.b.d[3].e", "root.f"],
        )
        self.assertEqual(
            FieldChecker.find_blank_values({"a": 0, "b": False}, "x"), []
        )

    def test_collect_text(self) -> None:
        """Text is gathered from nested values and numbers are skipped."""
        value = {"a": "Hello", "b": ["World", 5, {"c": "!"}]}
        self.assertEqual(CoverageChecker.collect_text(value), "Hello World  !")

    def test_each_checker_returns_check_results(self) -> None:
        """Every checker returns a list of passing CheckResult objects."""
        sections = load_sample("valid_brief.json")["sections"]
        expected_counts = (
            (HeadingChecker, 11),
            (FieldChecker, 67),
            (CoverageChecker, 28),
        )

        for checker_class, count in expected_counts:
            with self.subTest(checker=checker_class.__name__):
                results = checker_class(sections).check()

                self.assertEqual(len(results), count)
                for result in results:
                    self.assertIsInstance(result, CheckResult)
                    self.assertEqual(result.status, "PASS")


class TestHeadingChecker(unittest.TestCase):
    """Section count and headings, checked through HeadingChecker."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief's sections."""
        self.sections = load_sample("valid_brief.json")["sections"]

    def test_missing_last_section(self) -> None:
        """Nine sections fail the count and heading 10."""
        self.sections.pop()
        results = HeadingChecker(self.sections).check()

        self.assertEqual(len(failed(results, check="section count")), 1)
        missing = failed(results, check="heading", section="section 10")
        self.assertEqual(len(missing), 1)
        self.assertIn("Deliverable Checklist", missing[0].message)

    def test_extra_section(self) -> None:
        """An 11th section fails the count and is named as unexpected."""
        self.sections.append(
            {"number": 11, "heading": "Bonus Ideas", "content": {}}
        )
        results = HeadingChecker(self.sections).check()

        self.assertEqual(len(failed(results)), 2)
        extra = failed(results, check="heading")
        self.assertIn("Unexpected extra section", extra[0].message)

    def test_heading_problems_get_specific_messages(self) -> None:
        """Each kind of heading mistake is explained in its own way."""
        cases = {
            "Output Spec": "does not match",
            "output specification": "Wrong capital letters",
            "  Output Specification ": "extra spaces",
            "3. Output Specification": "number prefix",
        }
        for heading, expected_text in cases.items():
            with self.subTest(heading=heading):
                self.sections[2]["heading"] = heading
                results = HeadingChecker(self.sections).check()

                rows = failed(results, check="heading")
                self.assertEqual(len(rows), 1)
                self.assertIn(expected_text, rows[0].message)

    def test_get_section_raises_for_a_missing_section(self) -> None:
        """Asking for a section that is not there raises an exception."""
        checker = HeadingChecker(self.sections[:3])

        self.assertEqual(checker.get_section(2), self.sections[1])
        with self.assertRaises(MissingSectionError) as context:
            checker.get_section(4)
        self.assertEqual(
            context.exception.section_name, "Constraints & Assumptions"
        )


class TestFieldChecker(unittest.TestCase):
    """Fields, types, counts, extras and blanks, via FieldChecker."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief's sections."""
        self.sections = load_sample("valid_brief.json")["sections"]

    def run_check(self) -> list[CheckResult]:
        """Run FieldChecker on the current sections."""
        return FieldChecker(self.sections).check()

    def test_missing_required_field(self) -> None:
        """Removing 'role' from section 1 gives one failed field check."""
        del self.sections[0]["content"]["role"]
        rows = failed(self.run_check())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].check, "field")
        self.assertEqual(rows[0].section, "section 1")
        self.assertIn("role", rows[0].message)

    def test_wrong_type_stops_further_checks(self) -> None:
        """A text 'assumptions' fails the type check, with no count row."""
        self.sections[3]["content"]["assumptions"] = "just text"
        results = self.run_check()

        rows = failed(results)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].check, "type")
        counts = [
            result for result in results
            if result.section == "section 4" and result.check == "item count"
        ]
        self.assertEqual(counts, [])

    def test_item_count_limits(self) -> None:
        """Stretch goals: 1 and 4 fail, 2 and 3 are allowed."""
        for count, expected_failures in ((1, 1), (2, 0), (3, 0), (4, 1)):
            with self.subTest(goals=count):
                self.sections[8]["content"]["goals"] = ["goal"] * count
                self.assertEqual(
                    len(failed(self.run_check())), expected_failures
                )

    def test_empty_section_content(self) -> None:
        """An empty section 6 is missing all three of its fields."""
        self.sections[5]["content"] = {}
        rows = failed(self.run_check())

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row.check == "field" for row in rows))

    def test_extra_field_is_only_a_warning(self) -> None:
        """An unknown field is reported with severity 'warning'."""
        self.sections[0]["content"]["notes"] = "hello"
        rows = failed(self.run_check())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].check, "extra fields")
        self.assertEqual(rows[0].severity, "warning")
        self.assertIn("notes", rows[0].message)

    def test_blank_values_report_their_path(self) -> None:
        """Blanks are found in nested dictionaries and in lists."""
        self.sections[1]["content"]["fields"]["appointment_id"] = ""
        rows = failed(self.run_check(), check="blank values")
        self.assertEqual(len(rows), 1)
        self.assertIn("fields.appointment_id", rows[0].message)

        self.sections = load_sample("valid_brief.json")["sections"]
        self.sections[3]["content"]["assumptions"][1] = "   "
        rows = failed(self.run_check(), check="blank values")
        self.assertEqual(len(rows), 1)
        self.assertIn("assumptions[2]", rows[0].message)

    def test_generator_matches_check(self) -> None:
        """iter_results() yields exactly the rows that check() returns."""
        generator = FieldChecker(self.sections).iter_results()

        self.assertIsInstance(generator, types.GeneratorType)
        self.assertEqual(list(generator), self.run_check())

    def test_generator_is_lazy(self) -> None:
        """A broken section 9 is never reached if we stop early."""
        self.sections[8]["content"] = None
        generator = FieldChecker(self.sections).iter_results()

        first_ten = list(islice(generator, 10))
        self.assertEqual(len(first_ten), 10)
        with self.assertRaises(TypeError):
            list(FieldChecker(self.sections).iter_results())


class TestCoverageChecker(unittest.TestCase):
    """The Module 1-5 topic checks, via CoverageChecker."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief's sections."""
        self.sections = load_sample("valid_brief.json")["sections"]

    def test_text_is_lower_case_and_topics_are_covered(self) -> None:
        """The brief's text is lower-cased once, and all 28 topics pass."""
        checker = CoverageChecker(self.sections)

        self.assertEqual(checker.text, checker.text.lower())
        self.assertTrue(checker.covers(["decorator"]))
        self.assertFalse(checker.covers(["zzz-not-in-the-brief"]))
        results = checker.check()
        self.assertEqual(len(results), 28)
        self.assertEqual(failed(results), [])

    def test_missing_keyword_fails_that_topic(self) -> None:
        """Removing the only mention of recursion fails that topic."""
        steps = self.sections[4]["content"]["steps"]
        steps[6] = "Apply lambda, map(), filter() and reduce to the totals."

        rows = failed(CoverageChecker(self.sections).check())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].section, "module 2")
        self.assertIn("recursion", rows[0].message)

    def test_keywords_are_not_case_sensitive(self) -> None:
        """Upper-case text still counts as a mention of the topic."""
        steps = self.sections[4]["content"]["steps"]
        steps[6] = "Apply lambda, map(), filter(), reduce; use RECURSION."

        rows = failed(CoverageChecker(self.sections).check())
        self.assertEqual(rows, [])

class AlwaysFailChecker(BaseChecker):
    """A checker invented for a test: it always reports one failure."""

    name = "always"

    def check(self) -> list[CheckResult]:
        """Return a single failed result."""
        return [CheckResult.failed("brief", "custom", "always fails")]


class TestBriefValidator(unittest.TestCase):
    """Building a validator, its options, from_file and extension."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief."""
        self.brief = load_sample("valid_brief.json")

    def test_wrong_shapes_raise_exceptions(self) -> None:
        """Basic structure problems raise when the validator is built."""
        cases = [
            (["a list"], InvalidDataTypeError),
            ({"title": "x"}, MalformedRowError),
            ({"sections": "text"}, InvalidDataTypeError),
            ({"sections": ["oops"]}, InvalidDataTypeError),
            ({"sections": [{"heading": "A"}]}, MalformedRowError),
        ]
        for data, error_type in cases:
            with self.subTest(data=data):
                with self.assertRaises(error_type):
                    BriefValidator(data)

    def test_unknown_option_is_rejected(self) -> None:
        """A misspelled option raises TypeError and names the culprit."""
        with self.assertRaises(TypeError) as context:
            BriefValidator(self.brief, skip_coveage=True)
        self.assertIn("skip_coveage", str(context.exception))

    def test_class_attributes(self) -> None:
        """The checkers and options are listed on the class."""
        self.assertEqual(
            BriefValidator.CHECKER_CLASSES,
            (HeadingChecker, FieldChecker, CoverageChecker),
        )
        self.assertEqual(BriefValidator.KNOWN_OPTIONS, {"skip_coverage"})

    def test_validate_valid_brief(self) -> None:
        """A correct brief gives 106 passing results."""
        report = run(self.brief)

        self.assertIsInstance(report, ComplianceReport)
        self.assertEqual(len(report), 106)
        self.assertEqual(list(report.violations()), [])
        self.assertEqual(report.verdict, "COMPLIANT")
        self.assertEqual(report.score, 100.0)

    def test_file_name_on_report_and_rows(self) -> None:
        """The file name given to the validator reaches the report."""
        report = BriefValidator(self.brief, "my_brief.json").validate()

        self.assertEqual(report.file_name, "my_brief.json")
        names = {row["file"] for row in report.to_rows()}
        self.assertEqual(names, {"my_brief.json"})

    def test_strict_mode(self) -> None:
        """An extra field is a warning normally and an error when strict."""
        self.brief["sections"][0]["content"]["notes"] = "hello"

        normal = run(self.brief)
        strict = run(self.brief, strict=True)

        self.assertEqual(normal.verdict, "COMPLIANT")
        self.assertEqual(strict.verdict, "NON-COMPLIANT")
        severities = {result.severity for result in strict.violations()}
        self.assertEqual(severities, {"error"})

    def test_skip_coverage(self) -> None:
        """The skip_coverage option leaves out all 28 topic results."""
        self.assertEqual(len(run(self.brief, skip_coverage=True)), 78)

    def test_from_file(self) -> None:
        """from_file accepts text or a Path, and passes options on."""
        path = SAMPLE_DIR / "valid_brief.json"
        for source in (path, str(path)):
            with self.subTest(source=type(source).__name__):
                validator = BriefValidator.from_file(source)
                self.assertEqual(validator.file_name, "valid_brief.json")

        extra = SAMPLE_DIR / "extra_fields.json"
        strict = BriefValidator.from_file(extra, strict=True).validate()
        self.assertEqual(strict.verdict, "NON-COMPLIANT")

    def test_from_file_failures(self) -> None:
        """Unreadable files raise our own exceptions."""
        with tempfile.TemporaryDirectory() as folder:
            empty = Path(folder) / "empty.json"
            empty.write_text("", encoding="utf-8")
            broken = Path(folder) / "broken.json"
            broken.write_text('{ "title": ', encoding="utf-8")

            cases = [
                (Path(folder) / "nope.json", MissingFileError),
                (empty, EmptyInputError),
                (broken, MalformedRowError),
            ]
            for path, error_type in cases:
                with self.subTest(file=path.name):
                    with self.assertRaises(error_type):
                        BriefValidator.from_file(path)

    def test_from_file_builds_the_subclass(self) -> None:
        """A classmethod called on a subclass builds that subclass."""

        class CustomValidator(BriefValidator):
            """A subclass defined only for this test."""

        path = SAMPLE_DIR / "valid_brief.json"
        self.assertIsInstance(
            CustomValidator.from_file(path), CustomValidator
        )

    def test_new_checker_without_editing_validator(self) -> None:
        """Adding a checker needs only a new class and a new tuple."""

        class CustomValidator(BriefValidator):
            """Runs only the always-failing checker."""

            CHECKER_CLASSES = (AlwaysFailChecker,)

        report = CustomValidator(self.brief).validate()

        self.assertEqual(len(report), 1)
        self.assertEqual(len(list(report.violations())), 1)
        self.assertEqual(report.verdict, "NON-COMPLIANT")

    def test_timings_use_method_names(self) -> None:
        """Each checker's check() gets its own entry in TIMINGS."""
        TIMINGS.clear()
        run(self.brief)

        self.assertEqual(
            set(TIMINGS),
            {
                "HeadingChecker.check",
                "FieldChecker.check",
                "CoverageChecker.check",
            },
        )

    def test_adapter_function(self) -> None:
        """validate_brief_oop returns the same rows as the report."""
        rows = validate_brief_oop(self.brief, "x.json")
        report = BriefValidator(self.brief, "x.json").validate()

        self.assertEqual(rows, report.to_rows())
        self.assertEqual(len(rows), 106)
        self.assertIsInstance(rows[0], dict)


class TestSampleFilesOOP(unittest.TestCase):
    """Run the real sample files through the class-based pipeline."""

    # file name -> (total results, failed, errors, warnings)
    EXPECTED = {
        "valid_brief.json": (106, 0, 0, 0),
        "missing_section.json": (101, 3, 3, 0),
        "wrong_heading.json": (106, 1, 1, 0),
        "bad_type.json": (105, 1, 1, 0),
        "extra_fields.json": (106, 1, 0, 1),
    }

    def test_sample_files_give_the_expected_results(self) -> None:
        """Each sample file produces the documented numbers."""
        for name, (total, bad, errors, warnings) in self.EXPECTED.items():
            with self.subTest(file=name):
                report = BriefValidator.from_file(SAMPLE_DIR / name).validate()

                self.assertEqual(len(report), total)
                self.assertEqual(len(list(report.violations())), bad)
                self.assertEqual(len(list(report.violations("error"))), errors)
                self.assertEqual(
                    len(list(report.violations("warning"))), warnings
                )


if __name__ == "__main__":
    unittest.main()
