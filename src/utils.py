"""Utilities for handling the fixed 10-section blueprint, the Module 1-5 topic
checklist, and the functions that load and sanity-check a brief file.
"""

import functools
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable

from src.exceptions import (
    EmptyInputError,
    InvalidDataTypeError,
    MalformedRowError,
    MissingFileError,
)

logger = logging.getLogger("blueprint_checker")

TIMINGS: dict[str, float] = {}

# ------------------The blueprint: the 10 required sections, in order.-------------------------------
BLUEPRINT_RULES = {
    1: {
        "heading": "Business Scenario",
        "fields": {
            "role": {"type": str},
            "domain": {"type": str},
            "problem": {"type": str},
        },
    },
    2: {
        "heading": "Input Specification",
        "fields": {
            "format": {"type": str},
            "fields": {"type": dict},
        },
    },
    3: {
        "heading": "Output Specification",
        "fields": {
            "format": {"type": str},
            "fields": {"type": dict},
            "derivation": {"type": str},
        },
    },
    4: {
        "heading": "Constraints & Assumptions",
        "fields": {
            "assumptions": {"type": list, "min_items": 1},
        },
    },
    5: {
        "heading": "Core Task",
        "fields": {
            "description": {"type": str},
            "steps": {"type": list, "min_items": 1},
        },
    },
    6: {
        "heading": "Required Implementations",
        "fields": {
            "function_based": {"type": str},
            "class_based": {"type": str},
            "comparison": {"type": str},
        },
    },
    7: {
        "heading": "Error Handling Requirements",
        "fields": {
            "failure_cases": {"type": list, "min_items": 4},
        },
    },
    8: {
        "heading": "Testing Requirements",
        "fields": {
            "happy_path": {"type": str},
            "edge_cases": {"type": list, "min_items": 1},
            "failure_cases": {"type": list, "min_items": 1},
        },
    },
    9: {
        "heading": "Stretch Goals",
        "fields": {
            "goals": {"type": list, "min_items": 2, "max_items": 3},
        },
    },
    10: {
        "heading": "Deliverable Checklist",
        "fields": {
            "items": {"type": list, "min_items": 1},
        },
    },
}

EXPECTED_HEADINGS = tuple(rule["heading"] for rule in BLUEPRINT_RULES.values())

# -----------------The Module 1-5 curriculum checklist.-----------------------------
MODULE_TOPICS = {
    1: {
        "variables and types": ["variable", "numeric", "boolean"],
        "strings": ["string", "slicing"],
        "operators": ["operator", "bitwise"],
        "f-strings": ["f-string"],
        "control flow": ["if/elif", "for loop", "while loop"],
    },
    2: {
        "functions": ["default argument", "keyword argument", "*args", "**kwargs"],
        "lambda, map, filter, reduce": ["lambda", "map()", "filter()", "reduce"],
        "recursion": ["recursion", "recursive"],
        "data structures": ["tuple", "dictionar", "set operation"],
        "comprehensions": ["comprehension"],
    },
    3: {
        "modules and packages": ["module", "package"],
        "file handling": ["pathlib", "context manager", "with open"],
        "csv and json": ["csv", "json"],
        "str.format": ["str.format", ".format("],
        "pep 8": ["pep 8", "pep8"],
    },
    4: {
        "classes": ["class", "__init__"],
        "class and static methods": ["classmethod", "staticmethod",
                                     "class method", "static method"],
        "inheritance": ["inheritance", "super()"],
        "dunder methods": ["__str__", "__repr__", "__eq__", "dunder"],
        "exceptions": ["try/except", "custom exception", "finally"],
        "iterators and generators": ["iterator", "generator", "yield"],
        "closures and decorators": ["closure", "decorator"],
    },
    5: {
        "concurrency": ["concurrent.futures", "threadpoolexecutor",
                        "processpoolexecutor"],
        "unit testing": ["unittest", "pytest"],
        "external data source": ["sqlite", "external api"],
        "type hints": ["type hint", "typing"],
        "docstrings": ["docstring"],
        "project structure": ["project structure", "readme"],
    },
}


def load_brief(file_path: str | Path) -> Any:
    """Read a brief file and return JSON content. file_path contain path of json file."""
    path = Path(file_path)  

    if not path.is_file():
        raise MissingFileError(str(path))

    try:
        with open(path, "r", encoding="utf-8") as file:
            text = file.read()
    except UnicodeDecodeError as error:
        raise MalformedRowError("file is not valid UTF-8 text") from error

    if text.strip() == "":
        raise EmptyInputError(str(path))

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
            raise MalformedRowError(
            f"invalid JSON - {error.msg} "
            f"(line {error.lineno}, column {error.colno})"
        ) from error

    if data is None or data == {} or data == []:
        raise EmptyInputError(str(path))

    return data


def check_brief_shape(data: Any) -> None:
    """Check that loaded data has the basic structure of a brief."""
    if not isinstance(data, dict):
        raise InvalidDataTypeError("brief", "dict", data)

    if "sections" not in data:
        raise MalformedRowError("the key 'sections' is missing", "brief")

    sections = data["sections"]
    if not isinstance(sections, list):
        raise InvalidDataTypeError("sections", "list", sections)

    for position, entry in enumerate(sections, start=1):
        where = f"section {position}"

        if not isinstance(entry, dict):
            raise InvalidDataTypeError(where, "dict", entry)

        for key in ("heading", "content"):
            if key not in entry:
                raise MalformedRowError(f"the key '{key}' is missing", where)

        if not isinstance(entry["heading"], str):
            raise InvalidDataTypeError(
                f"heading of {where}", "str", entry["heading"]
            )

        if not isinstance(entry["content"], dict):
            raise InvalidDataTypeError(
                f"content of {where}", "dict", entry["content"]
            )
        
def timed(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: record how long each call to func takes in TIMINGS."""

    @functools.wraps(func)  
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Run func, then store how long it took."""
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            TIMINGS[func.__qualname__] = time.perf_counter() - start

    return wrapper


def logged(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: log the start and end of a validation step."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Log the start and end of the call to func."""
        logger.debug("Starting %s", func.__qualname__)
        result = func(*args, **kwargs)
        logger.debug("Finished %s: %d rows", func.__qualname__, len(result))
        return result

    return wrapper