"""Unit tests for the function-based validator and the file loader.

Run all tests from the project root with:
    python -m unittest discover -v
"""

import tempfile
import unittest
from itertools import islice
from pathlib import Path
from typing import Any

from src.exceptions import (
    BriefCheckerError,
    EmptyInputError,
    InvalidDataTypeError,
    MalformedRowError,
    MissingFileError,
)
from src.utils import load_brief
from src.validator import (
    ALL_OK,
    HEADING_OK,
    add_file_name,
    collect_text,
    describe_mask,
    find_blank_values,
    iter_field_results,
    iter_violations,
    make_result,
    section_status_masks,
    tally_results,
    validate_brief,
    validate_fields,
)
from tests.helpers import SAMPLE_DIR, failures, load_sample


def run(brief: dict[str, Any], **options: Any) -> list[dict[str, str]]:
    """Validate a brief as 'test.json' and return the result rows.

    Args:
        brief: The brief dictionary to validate.
        **options: Passed on to validate_brief (strict, skip_coverage).

    Returns:
        The result rows.
    """
    return validate_brief(brief, "test.json", **options)

class TestHappyPath(unittest.TestCase):
    """A correct brief should pass every check."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief before every test."""
        self.brief = load_sample("valid_brief.json")

    def test_valid_brief_has_no_failures(self) -> None:
        """No row of a correct brief has the status FAIL."""
        self.assertEqual(failures(run(self.brief)), [])

    def test_valid_brief_check_counts(self) -> None:
        """11 structure + 67 field + 28 topic checks, all passing."""
        results = run(self.brief)
        self.assertEqual(tally_results(results), {"PASS": 106, "FAIL": 0})

    def test_every_row_has_the_expected_keys(self) -> None:
        """Each row carries exactly the six agreed keys."""
        expected = {
            "file", "section", "check", "status", "severity", "message",
        }
        for row in run(self.brief):
            self.assertEqual(set(row), expected)

    def test_file_name_is_stamped_on_every_row(self) -> None:
        """The file name given to validate_brief ends up on every row."""
        results = validate_brief(self.brief, "my_brief.json")
        names = {row["file"] for row in results}
        self.assertEqual(names, {"my_brief.json"})


class TestStructure(unittest.TestCase):
    """Section count and heading checks."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief before every test."""
        self.brief = load_sample("valid_brief.json")

    def test_missing_last_section(self) -> None:
        """A brief with 9 sections fails the count and heading 10."""
        self.brief["sections"].pop()
        results = run(self.brief)

        self.assertEqual(len(failures(results, check="section count")), 1)
        missing = failures(results, check="heading", section="section 10")
        self.assertEqual(len(missing), 1)
        self.assertIn("Deliverable Checklist", missing[0]["message"])

    def test_extra_section(self) -> None:
        """An 11th section fails the count and is named as unexpected."""
        self.brief["sections"].append(
            {"number": 11, "heading": "Bonus Ideas", "content": {}}
        )
        results = run(self.brief)

        self.assertEqual(len(failures(results)), 2)
        extra = failures(results, check="heading")
        self.assertIn("Unexpected extra section", extra[0]["message"])

    def test_no_sections_at_all(self) -> None:
        """An empty sections list fails the count and all 10 headings."""
        results = run({"sections": []}, skip_coverage=True)
        self.assertEqual(len(results), 11)
        self.assertEqual(len(failures(results)), 11)

    def test_heading_problems_get_specific_messages(self) -> None:
        """Each kind of heading mistake is explained in its own way."""
        cases = {
            "Output Spec": "does not match",
            "output specification": "Wrong capital letters",
            "  Output Specification ": "extra spaces",
            "3. Output Specification": "number prefix",
            "Output Specification:": "trailing colon",
            "": "does not match",
        }
        for heading, expected_text in cases.items():
            with self.subTest(heading=heading):
                self.brief["sections"][2]["heading"] = heading
                rows = failures(run(self.brief), check="heading")
                self.assertEqual(len(rows), 1)
                self.assertIn(expected_text, rows[0]["message"])

    def test_swapped_sections_are_reported_as_wrong_order(self) -> None:
        """Sections 3 and 4 swapped give two 'Wrong order' failures."""
        sections = self.brief["sections"]
        sections[2], sections[3] = sections[3], sections[2]

        rows = failures(run(self.brief), check="heading")
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn("Wrong order", row["message"])

class TestFields(unittest.TestCase):
    """Required fields, types, item counts, extras and blank values."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief before every test."""
        self.brief = load_sample("valid_brief.json")

    def fields_only(self) -> list[dict[str, str]]:
        """Validate self.brief without the topic-coverage checks.

        Changing a field's text can also remove a curriculum keyword, so
        skipping coverage keeps each test about one thing only.
        """
        return run(self.brief, skip_coverage=True)

    def test_missing_required_field(self) -> None:
        """Removing 'role' from section 1 gives one failed field check."""
        del self.brief["sections"][0]["content"]["role"]
        rows = failures(self.fields_only())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["check"], "field")
        self.assertEqual(rows[0]["section"], "section 1")
        self.assertIn("role", rows[0]["message"])

    def test_wrong_type_stops_further_checks(self) -> None:
        """A text 'assumptions' fails the type check, with no count row."""
        self.brief["sections"][3]["content"]["assumptions"] = "just text"
        results = self.fields_only()

        rows = failures(results)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["check"], "type")
        counts = [
            row for row in results
            if row["section"] == "section 4" and row["check"] == "item count"
        ]
        self.assertEqual(counts, [])

    def test_too_few_items(self) -> None:
        """Two failure cases are below the minimum of four."""
        self.brief["sections"][6]["content"]["failure_cases"] = ["a", "b"]
        rows = failures(self.fields_only())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["check"], "item count")
        self.assertIn("at least 4", rows[0]["message"])

    def test_too_many_items(self) -> None:
        """Five stretch goals are above the maximum of three."""
        self.brief["sections"][8]["content"]["goals"] = ["g"] * 5
        rows = failures(self.fields_only())

        self.assertEqual(len(rows), 1)
        self.assertIn("at most 3", rows[0]["message"])

    def test_limits_are_inclusive(self) -> None:
        """Exactly 2 and exactly 3 stretch goals are both allowed."""
        content = self.brief["sections"][8]["content"]
        for count in (2, 3):
            with self.subTest(items=count):
                content["goals"] = ["goal"] * count
                self.assertEqual(failures(self.fields_only()), [])

    def test_empty_section_content(self) -> None:
        """An empty section 6 is missing all three of its fields."""
        self.brief["sections"][5]["content"] = {}
        rows = failures(self.fields_only())

        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["check"] == "field" for row in rows))

    def test_extra_field_is_only_a_warning(self) -> None:
        """An unknown field is reported with severity 'warning'."""
        self.brief["sections"][0]["content"]["notes"] = "hello"
        rows = failures(self.fields_only())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["check"], "extra fields")
        self.assertEqual(rows[0]["severity"], "warning")
        self.assertIn("notes", rows[0]["message"])

    def test_blank_value_in_nested_dictionary(self) -> None:
        """A blank value deep inside 'fields' is found with its path."""
        fields = self.brief["sections"][1]["content"]["fields"]
        fields["appointment_id"] = ""
        rows = failures(self.fields_only())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["check"], "blank values")
        self.assertIn("fields.appointment_id", rows[0]["message"])

    def test_blank_value_in_list(self) -> None:
        """A blank list item is reported by its 1-based position."""
        assumptions = self.brief["sections"][3]["content"]["assumptions"]
        assumptions[1] = "   "
        rows = failures(self.fields_only())

        self.assertEqual(len(rows), 1)
        self.assertIn("assumptions[2]", rows[0]["message"])

    def test_missing_sections_are_skipped(self) -> None:
        """Field checks run only for the sections that exist."""
        rows = validate_fields(self.brief["sections"][:3])

        self.assertEqual(failures(rows), [])
        seen = {row["section"] for row in rows}
        self.assertEqual(seen, {"section 1", "section 2", "section 3"})


class TestCoverage(unittest.TestCase):
    """The Module 1-5 topic checks."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief before every test."""
        self.brief = load_sample("valid_brief.json")

    def topic_rows(self) -> list[dict[str, str]]:
        """Return only the topic-coverage rows for self.brief."""
        return [
            row for row in run(self.brief)
            if row["check"] == "topic coverage"
        ]

    def test_valid_brief_covers_every_topic(self) -> None:
        """All 28 topics are found in the valid brief."""
        rows = self.topic_rows()
        self.assertEqual(len(rows), 28)
        self.assertTrue(all(row["status"] == "PASS" for row in rows))

    def test_missing_keyword_fails_that_topic(self) -> None:
        """Removing the only mention of recursion fails that topic."""
        steps = self.brief["sections"][4]["content"]["steps"]
        # Step 7 is the only text that mentions recursion.
        steps[6] = "Apply lambda, map(), filter() and reduce to the totals."

        rows = failures(run(self.brief), check="topic coverage")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["section"], "module 2")
        self.assertIn("recursion", rows[0]["message"])

    def test_keywords_are_not_case_sensitive(self) -> None:
        """Upper-case text still counts as a mention of the topic."""
        steps = self.brief["sections"][4]["content"]["steps"]
        steps[6] = "Apply lambda, map(), filter(), reduce; use RECURSION."

        rows = failures(run(self.brief), check="topic coverage")
        self.assertEqual(rows, [])

    def test_skip_coverage_removes_topic_rows(self) -> None:
        """The skip_coverage option leaves out all 28 topic rows."""
        results = run(self.brief, skip_coverage=True)

        self.assertEqual(len(results), 78)
        topics = [r for r in results if r["check"] == "topic coverage"]
        self.assertEqual(topics, [])

class TestOptionsAndShape(unittest.TestCase):
    """validate_brief options, and briefs with a broken basic shape."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief before every test."""
        self.brief = load_sample("valid_brief.json")

    def test_strict_mode_turns_warnings_into_errors(self) -> None:
        """An extra field is a warning normally and an error when strict."""
        self.brief["sections"][0]["content"]["notes"] = "hello"

        normal = failures(run(self.brief))
        strict = failures(run(self.brief, strict=True))

        self.assertEqual(normal[0]["severity"], "warning")
        self.assertEqual(strict[0]["severity"], "error")

    def test_unknown_option_is_rejected(self) -> None:
        """A misspelled option raises TypeError instead of being ignored."""
        with self.assertRaises(TypeError) as context:
            validate_brief(self.brief, skip_coveage=True)
        self.assertIn("skip_coveage", str(context.exception))

    def test_wrong_shapes_raise_the_right_exception(self) -> None:
        """Basic structure problems raise exceptions, not result rows."""
        cases = [
            (["a list"], InvalidDataTypeError),
            ({"title": "x"}, MalformedRowError),
            ({"sections": "text"}, InvalidDataTypeError),
            ({"sections": ["oops"]}, InvalidDataTypeError),
            ({"sections": [{"heading": "A"}]}, MalformedRowError),
            ({"sections": [{"heading": 5, "content": {}}]},
             InvalidDataTypeError),
            ({"sections": [{"heading": "A", "content": "text"}]},
             InvalidDataTypeError),
        ]
        for data, error_type in cases:
            with self.subTest(data=data):
                with self.assertRaises(error_type):
                    validate_brief(data)

    def test_exception_carries_details(self) -> None:
        """The exception object stores what was expected and what came."""
        with self.assertRaises(InvalidDataTypeError) as context:
            validate_brief({"sections": "text"})

        error = context.exception
        self.assertEqual(error.field_name, "sections")
        self.assertEqual(error.expected, "list")
        self.assertEqual(error.actual, "str")


class TestBitmasks(unittest.TestCase):
    """The per-section status bitmasks."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief before every test."""
        self.brief = load_sample("valid_brief.json")

    def test_valid_brief_masks_are_all_ok(self) -> None:
        """Every one of the 10 sections has all four bits on."""
        masks = section_status_masks(run(self.brief))

        self.assertEqual(len(masks), 10)
        self.assertTrue(all(mask == ALL_OK for mask in masks.values()))

    def test_heading_failure_switches_off_only_the_heading_bit(self) -> None:
        """A bad heading in section 3 turns off bit 0 and nothing else."""
        self.brief["sections"][2]["heading"] = "Output Spec"
        masks = section_status_masks(run(self.brief))

        self.assertEqual(masks["section 3"], ALL_OK & ~HEADING_OK)
        self.assertEqual(masks["section 3"], 14)
        self.assertEqual(describe_mask(masks["section 3"]), ["heading"])
        self.assertEqual(masks["section 1"], ALL_OK)

    def test_warning_leaves_the_mask_unchanged(self) -> None:
        """Warnings never switch a bit off."""
        self.brief["sections"][0]["content"]["notes"] = "hello"
        masks = section_status_masks(run(self.brief))
        self.assertEqual(masks["section 1"], ALL_OK)

    def test_describe_mask(self) -> None:
        """Switched-off bits are named in a fixed order."""
        self.assertEqual(describe_mask(15), [])
        self.assertEqual(describe_mask(3), ["types", "content"])
        self.assertEqual(
            describe_mask(0), ["heading", "fields", "types", "content"]
        )


class TestHelpers(unittest.TestCase):
    """Small pure functions, tested with hand-made data."""

    def test_find_blank_values_goes_deep(self) -> None:
        """The recursive function finds blanks at every depth."""
        sample = {
            "a": "ok",
            "b": {"c": "", "d": ["x", None, {"e": " "}]},
            "f": [],
        }
        self.assertEqual(
            find_blank_values(sample, "root"),
            ["root.b.c", "root.b.d[2]", "root.b.d[3].e", "root.f"],
        )

    def test_zero_and_false_are_not_blank(self) -> None:
        """Only None, empty text and empty containers count as blank."""
        self.assertEqual(find_blank_values({"a": 0, "b": False}, "x"), [])

    def test_collect_text(self) -> None:
        """Text is gathered from nested values and numbers are skipped."""
        value = {"a": "Hello", "b": ["World", 5, {"c": "!"}]}
        self.assertEqual(collect_text(value), "Hello World  !")

    def test_tally_starts_from_zero_each_time(self) -> None:
        """Two calls with the same rows give the same counts."""
        rows = [
            make_result("brief", "x", True, "ok"),
            make_result("brief", "x", False, "bad"),
        ]
        expected = {"PASS": 1, "FAIL": 1}

        first = tally_results(rows)
        self.assertEqual(first, expected)
        second = tally_results(rows)
        self.assertEqual(second, expected)

    def test_make_result_forces_info_on_pass(self) -> None:
        """A passing row is always 'info', and a failing row keeps its own."""
        row = make_result("brief", "x", True, "ok", severity="error")
        self.assertEqual(row["status"], "PASS")
        self.assertEqual(row["severity"], "info")

        row = make_result("brief", "x", False, "bad")
        self.assertEqual(row["severity"], "error")

    def test_add_file_name_leaves_originals_alone(self) -> None:
        """Stamping a file name creates new rows."""
        original = [make_result("brief", "x", True, "ok")]
        stamped = add_file_name(original, "a.json")

        self.assertEqual(stamped[0]["file"], "a.json")
        self.assertNotIn("file", original[0])


class TestGenerators(unittest.TestCase):
    """The lazy (generator) versions of the checks."""

    def setUp(self) -> None:
        """Load a fresh copy of the valid brief before every test."""
        self.brief = load_sample("valid_brief.json")

    def test_generator_matches_the_list_version(self) -> None:
        """Collecting the generator gives exactly validate_fields()."""
        sections = self.brief["sections"]
        self.assertEqual(
            list(iter_field_results(sections)), validate_fields(sections)
        )

    def test_generator_is_lazy(self) -> None:
        """Work happens only when rows are requested."""
        # Calling the generator function is safe even if section 1 is broken...
        self.brief["sections"][0]["content"] = None
        generator = iter_field_results(self.brief["sections"])
        # ...the error appears only when the first row is requested.
        with self.assertRaises(TypeError):
            next(generator)

        # A broken section 9 is never reached if we stop after 10 rows.
        sections = load_sample("valid_brief.json")["sections"]
        sections[8]["content"] = None
        first_ten = list(islice(iter_field_results(sections), 10))
        self.assertEqual(len(first_ten), 10)
        with self.assertRaises(TypeError):
            list(iter_field_results(sections))

    def test_iter_violations_is_used_up(self) -> None:
        """A generator can be consumed only once."""
        self.brief["sections"][2]["heading"] = "Output Spec"
        violations = iter_violations(run(self.brief))

        self.assertEqual(len(list(violations)), 1)
        self.assertEqual(list(violations), [])

class TestLoading(unittest.TestCase):
    """Loading a file must fail cleanly, with the right exception."""

    def setUp(self) -> None:
        """Create a temporary folder for the files these tests write."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        """Delete the temporary folder and everything in it."""
        self.temp_dir.cleanup()

    def write(self, name: str, text: str) -> Path:
        """Write text to a file in the temporary folder.

        Args:
            name: The file name.
            text: The content to write.

        Returns:
            The path of the new file.
        """
        path = self.folder / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_loads_a_valid_file(self) -> None:
        """A good file loads, whether given as a Path or as text."""
        path = SAMPLE_DIR / "valid_brief.json"
        from_path = load_brief(path)
        from_text = load_brief(str(path))

        self.assertEqual(len(from_path["sections"]), 10)
        self.assertEqual(from_path, from_text)

    def test_missing_file(self) -> None:
        """A file that does not exist raises MissingFileError."""
        missing = self.folder / "nope.json"
        with self.assertRaises(MissingFileError) as context:
            load_brief(missing)
        self.assertEqual(context.exception.file_path, str(missing))

    def test_a_folder_is_not_a_file(self) -> None:
        """Passing a folder is reported as a missing file."""
        with self.assertRaises(MissingFileError):
            load_brief(self.folder)

    def test_empty_files_raise_empty_input_error(self) -> None:
        """Blank files and JSON that holds nothing count as empty."""
        contents = ["", "   \n\n", "{}", "[]", "null"]
        for number, text in enumerate(contents):
            with self.subTest(text=text):
                path = self.write(f"empty_{number}.json", text)
                with self.assertRaises(EmptyInputError):
                    load_brief(path)

    def test_malformed_json(self) -> None:
        """Cut-off JSON raises MalformedRowError and says why."""
        path = self.write("broken.json", '{ "title": "x", "sections": [ ')
        with self.assertRaises(MalformedRowError) as context:
            load_brief(path)
        self.assertIn("invalid JSON", str(context.exception))

    def test_file_that_is_not_utf8(self) -> None:
        """Binary junk is reported as malformed, not as a crash."""
        path = self.folder / "binary.json"
        path.write_bytes(b"\xff\xfe\x00\x01")
        with self.assertRaises(MalformedRowError) as context:
            load_brief(path)
        self.assertIn("UTF-8", str(context.exception))

    def test_all_our_errors_share_a_base_class(self) -> None:
        """One 'except BriefCheckerError' catches every loading failure."""
        empty = self.write("empty.json", "")
        for path in (self.folder / "nope.json", empty):
            with self.subTest(path=path.name):
                with self.assertRaises(BriefCheckerError):
                    load_brief(path)


class TestSampleFiles(unittest.TestCase):
    """Run the real sample files through the whole pipeline."""

    # A class attribute: shared by all tests in this class.
    # file name -> (total rows, failed rows, errors, warnings)
    EXPECTED = {
        "valid_brief.json": (106, 0, 0, 0),
        "missing_section.json": (101, 3, 3, 0),
        "wrong_heading.json": (106, 1, 1, 0),
        "bad_type.json": (105, 1, 1, 0),
        "extra_fields.json": (106, 1, 0, 1),
    }

    def test_sample_files_give_the_expected_results(self) -> None:
        """Each sample file produces the documented number of rows."""
        for name, (total, failed, errors, warnings) in self.EXPECTED.items():
            with self.subTest(file=name):
                results = validate_brief(load_brief(SAMPLE_DIR / name), name)

                self.assertEqual(len(results), total)
                self.assertEqual(len(failures(results)), failed)
                self.assertEqual(
                    len(failures(results, severity="error")), errors
                )
                self.assertEqual(
                    len(failures(results, severity="warning")), warnings
                )


if __name__ == "__main__":
    unittest.main()
