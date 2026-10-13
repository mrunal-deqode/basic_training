import copy

from src.exceptions import BriefCheckerError, MissingFileError
from src.utils import TIMINGS, load_brief
from src.validator import validate_brief
from src.validator_oop import (
    BriefValidator,
    CheckResult,
    CoverageChecker,
    FieldChecker,
    HeadingChecker,
    validate_brief_oop,
)

brief = load_brief("sample_data/valid_brief.json")

# 1. The dunder methods of CheckResult
a = CheckResult.failed("section 3", "heading", "Bad heading")
b = CheckResult("section 3", "heading", "FAIL", "error", "Bad heading")
c = CheckResult.passed("section 3", "heading", "Fine")
print("1.", a)
print(f"   {a!r}")
print("   a == b:", a == b)
print("   a == c:", a == c)
print("   a == 'text':", a == "text")
print("   passed() always gives severity:", c.severity)
try:
    CheckResult("s", "c", "MAYBE", "error", "m")
except ValueError as error:
    print(f"   {error}")
try:
    hash(a)
except TypeError as error:
    print(f"   {error}")
print()

# 2. Class attributes and instance attributes
print("2. Class attributes :", HeadingChecker.name, FieldChecker.name,
      CoverageChecker.name)
print("   Inherited rules  :", len(HeadingChecker.RULES), "sections")
print("   An instance      :", HeadingChecker([]))
print("   Own attribute    :", len(HeadingChecker([]).lower_headings),
      "lower-case headings")
print()

# 3. Do both versions produce identical rows?
print("3. Same rows as the function version?")
for name in ("valid_brief.json", "missing_section.json",
             "wrong_heading.json", "bad_type.json", "extra_fields.json"):
    data = load_brief(f"sample_data/{name}")
    rows_function = validate_brief(data, name)
    rows_oop = validate_brief_oop(data, name)
    print(f"   {name:<22} {len(rows_oop):>3} rows, "
          f"identical: {rows_function == rows_oop}")
print()

# 4. The report object
messy_data = copy.deepcopy(brief)
messy_data["sections"][2]["heading"] = "Output Spec"
del messy_data["sections"][0]["content"]["role"]
messy_data["sections"][3]["content"]["assumptions"] = "x"
messy_data["sections"][6]["content"]["failure_cases"] = ["a"]

messy = BriefValidator(messy_data, "messy_brief.json").validate()
print("4.", messy)
print(f"   {messy!r}")
print("   results   :", len(messy), "| score:", messy.score)
print("   violations:", [result.section for result in messy.violations()])
print("   first     :", next(messy.violations()).message)
iterator = iter(messy)
print("   iterator  :", type(iterator).__name__, "->", next(iterator).section)
print("   reusable  :", len(list(messy)), len(list(messy)))
print("   rows      :", messy.to_rows()[0]["file"])
print()

# 5. Class methods
valid = BriefValidator.from_file("sample_data/valid_brief.json").validate()
print("5. from_file    :", len(valid), "rows,", valid.file_name)
try:
    BriefValidator.from_file("sample_data/nope.json")
except MissingFileError as error:
    print("   missing file :", error)
row = messy.results[0].to_dict()
print("   from_dict    :", CheckResult.from_dict(row) == messy.results[0])
print()

# 6. Strict mode and options
extra = copy.deepcopy(brief)
extra["sections"][0]["content"]["notes"] = "hello"
print("6. normal      :", BriefValidator(extra).validate().verdict)
print("   strict      :", BriefValidator(extra, strict=True).validate().verdict)
print("   strict rows identical:",
      validate_brief_oop(extra, strict=True)
      == validate_brief(extra, strict=True))
print("   no coverage :",
      len(BriefValidator(brief, skip_coverage=True).validate()), "rows")
try:
    BriefValidator(brief, skip_coveage=True)
except TypeError as error:
    print(f"   TypeError: {error}")
try:
    BriefValidator({"title": "no sections here"})
except BriefCheckerError as error:
    print(f"   {type(error).__name__}: {error}")
print()

# 7. The decorators on methods
TIMINGS.clear()
BriefValidator(brief).validate()
print("7. Timed steps :", list(TIMINGS))
print("   Method name  :", HeadingChecker.check.__qualname__)