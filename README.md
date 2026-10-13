# Blueprint Compliance Checker

A command-line tool that checks a generated capstone project brief (a
JSON file) against a fixed 10-section blueprint and the Module 1-5
curriculum checklist, and writes a compliance report as CSV and JSON.

The checker is implemented **twice**: once with plain functions
(`src/validator.py`) and once with classes (`src/validator_oop.py`).
Both give identical results (see "Design comparison").

## Requirements

* Python 3.10 or newer
* Standard library only (nothing to install)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Usage

```bash
python main.py sample_data/valid_brief.json
python main.py sample_data/wrong_heading.json my_reports --impl oop
python main.py sample_data/extra_fields.json --strict
python main.py sample_data/valid_brief.json --verbose
python main.py            # no file given: the program asks for a path
```

| Argument | Meaning |
|---|---|
| `input_file` | the brief JSON file (asked for if left out) |
| `output_dir` | folder for the reports (default `output`) |
| `--impl function\|oop` | which implementation to run (default `function`) |
| `--strict` | treat warnings (such as extra fields) as errors |
| `--verbose` | show debug logging and the time each step took |

Two report files are written for each brief:
`<name>_report.csv` and `<name>_report.json`.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | checked, compliant |
| 1 | checked, non-compliant |
| 2 | no input file given |
| 3 | the file could not be checked (missing, empty, malformed, wrong types) |
| 4 | the reports could not be written |
| 130 | cancelled with Ctrl+C |

## Input format

```json
{
  "title": "Clinic Appointment No-Show Report",
  "sections": [
    {
      "number": 1,
      "heading": "Business Scenario",
      "content": {"role": "...", "domain": "...", "problem": "..."}
    }
  ]
}
```

A brief has a `title` and a `sections` list. Each section has a `number`,
a `heading` and a `content` dictionary. See `sample_data/valid_brief.json`.

## The blueprint

| # | Heading | Required fields |
|---|---|---|
| 1 | Business Scenario | role, domain, problem |
| 2 | Input Specification | format, fields |
| 3 | Output Specification | format, fields, derivation |
| 4 | Constraints & Assumptions | assumptions (at least 1) |
| 5 | Core Task | description, steps (at least 1) |
| 6 | Required Implementations | function_based, class_based, comparison |
| 7 | Error Handling Requirements | failure_cases (at least 4) |
| 8 | Testing Requirements | happy_path, edge_cases, failure_cases |
| 9 | Stretch Goals | goals (2 or 3) |
| 10 | Deliverable Checklist | items (at least 1) |

## What is checked

1. **Structure:** exactly 10 sections, in order, with the exact headings.
   Mistakes get specific messages (wrong capitals, extra spaces, number
   prefix, trailing colon, wrong order).
2. **Fields:** every required field is present, has the right type and an
   allowed number of items. Unknown fields are a *warning*. Blank values
   anywhere inside a section are an error.
3. **Curriculum coverage:** each of the 28 Module 1-5 topics must be
   mentioned somewhere in the brief (keyword search, case-insensitive).

Problems with the basic shape of the file (missing, empty or malformed
JSON, wrong types) raise custom exceptions. Everything else is a row in the
report.

## Output

CSV columns: `file, section, check, status, severity, message`.
The JSON file holds a `summary` object and the list of `results`.

* **Score** = passed checks / all checks, as a percentage.
* **Verdict**: `COMPLIANT` (no errors; warnings are allowed),
  `NON-COMPLIANT` (at least one error) or `NOT CHECKED` (nothing ran).

## Project structure

```
blueprint_checker/
├── main.py                  entry point
├── src/
│   ├── exceptions.py        five custom exceptions
│   ├── utils.py             rules, topic checklist, loading, decorators
│   ├── validator.py         function-based solution
│   ├── validator_oop.py     class-based solution
│   └── report.py            score, verdict, CSV and JSON writers
├── tests/                   unit, parity and golden-file tests
├── tools/                   style checker and checklist audit
└── sample_data/             example briefs and expected/ reports
```

## Running the tests

```bash
python -m unittest discover -v
python tools/check_style.py
bash tools/audit_checklist.sh
```

To recreate the expected reports after an intended change:

```bash
for name in valid_brief missing_section wrong_heading bad_type extra_fields; do
    python main.py sample_data/$name.json sample_data/expected > /dev/null
done
git diff sample_data/expected      # review before committing
```

## Design comparison

| | Function-based | Class-based |
|---|---|---|
| A check result | a dictionary with five keys (a typo in a key is not caught) | a `CheckResult` object, validated in `__init__` |
| State | passed as arguments; a closure remembers the brief's text | kept in `self` (`sections`, `text`) |
| Adding a new kind of check | write a function and call it in `validate_brief` | write a `BaseChecker` subclass and add it to `CHECKER_CLASSES` |
| Lazy output | generators (`iter_field_results`, `iter_violations`) | `violations()` generator and a hand-written `ResultIterator` |
| Printing and comparing results | dictionaries only | `__str__`, `__repr__`, `__eq__`, `__len__`, `__iter__` |
| Testing | call each small function with plain data | build an object first, or subclass it in a test |
| Size | shorter (compare with `wc -l src/validator*.py`) | longer, with more structure |

Both versions return the same list of row dictionaries, so `report.py` is
shared. `tests/test_parity.py` runs 22 broken briefs through both
versions and requires identical rows.

**Which one to choose?** For a checker this size the function version is
enough: it is shorter and easier to read from top to bottom. The class
version pays off when the number of check types grows, when checks need
their own settings, or when results should behave like real objects. The
shared parts (`report.py`, `utils.py`) show that the two styles can live
side by side.

## Limitations

* Curriculum coverage is a keyword search. A brief that mentions a word
  without really requiring the topic still counts as covering it.
* Required fields are matched by section position, not by heading.

## Stretch goals

* Check many briefs in parallel with `concurrent.futures` (planned).
* Store compliance history in SQLite (planned).