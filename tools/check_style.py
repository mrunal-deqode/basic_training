"""A small style checker for this project (standard library only).

It checks the rules that are easy to check by machine:

* lines are at most 79 characters long
* no trailing spaces and no tab characters
* every file ends with exactly one newline
* every module, class and function has a docstring
* every function has type hints (parameters and return value)
* no import is left unused

Run it from the project root:
    python tools/check_style.py
"""

import ast
import sys
from pathlib import Path

MAX_LINE_LENGTH = 79
FOLDERS = ("src", "tests", "tools")

# A problem is a pair: (line number, message).
Problem = tuple[int, str]


def find_python_files(root: Path) -> list[Path]:
    """Return every Python file the checker should look at.

    Args:
        root: The project root folder.

    Returns:
        main.py plus all .py files in src/, tests/ and tools/.
    """
    files = [root / "main.py"]
    for folder in FOLDERS:
        files.extend(sorted((root / folder).glob("*.py")))
    return files


def check_text(text: str) -> list[Problem]:
    """Check the rules that only need the raw text of a file.

    Args:
        text: The whole content of one file.

    Returns:
        The problems found.
    """
    problems = []

    for number, line in enumerate(text.split("\n"), start=1):
        if len(line) > MAX_LINE_LENGTH:
            problems.append(
                (number, f"line too long ({len(line)} > {MAX_LINE_LENGTH})")
            )
        if line != line.rstrip():
            problems.append((number, "trailing whitespace"))
        if "\t" in line:
            problems.append((number, "tab character"))

    if not text.endswith("\n"):
        problems.append((text.count("\n") + 1, "no newline at end of file"))
    elif text.endswith("\n\n"):
        problems.append((text.count("\n"), "blank line at end of file"))

    return problems


def check_hints(node: ast.FunctionDef) -> list[Problem]:
    """Check that a function has type hints on everything.

    Args:
        node: The parsed function.

    Returns:
        The problems found.
    """
    problems = []
    arguments = node.args

    # Adding lists with + creates a NEW list, so append() below is safe.
    every_argument = (
        arguments.posonlyargs + arguments.args + arguments.kwonlyargs
    )
    if arguments.vararg is not None:  # *args
        every_argument.append(arguments.vararg)
    if arguments.kwarg is not None:  # **kwargs
        every_argument.append(arguments.kwarg)

    for argument in every_argument:
        if argument.arg in ("self", "cls"):
            continue
        if argument.annotation is None:
            problems.append(
                (node.lineno,
                 f"no type hint for '{argument.arg}' in {node.name}")
            )

    if node.returns is None:
        problems.append((node.lineno, f"no return type hint: {node.name}"))

    return problems


def check_docstrings_and_hints(tree: ast.Module) -> list[Problem]:
    """Check docstrings on everything, and type hints on functions.

    Args:
        tree: The parsed file.

    Returns:
        The problems found.
    """
    problems = []

    if ast.get_docstring(tree) is None:
        problems.append((1, "missing module docstring"))

    definition_types = (ast.FunctionDef, ast.ClassDef)

    for node in ast.walk(tree):  # visits nested functions and classes too
        if not isinstance(node, definition_types):
            continue

        if ast.get_docstring(node) is None:
            problems.append((node.lineno, f"missing docstring: {node.name}"))

        if isinstance(node, ast.FunctionDef):
            problems.extend(check_hints(node))

    return problems


def check_unused_imports(tree: ast.Module) -> list[Problem]:
    """Find names that are imported but never used.

    Args:
        tree: The parsed file.

    Returns:
        The problems found.
    """
    imported = {}  # name -> line number of the import
    used = set()  # every plain name that appears anywhere in the code

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imported[name] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported[alias.asname or alias.name] = node.lineno
        elif isinstance(node, ast.Name):
            used.add(node.id)

    return [
        (line, f"'{name}' imported but never used")
        for name, line in imported.items()
        if name not in used
    ]


def main() -> int:
    """Check every project file and print the problems.

    Returns:
        0 if everything is fine, 1 if any problem was found.
    """
    root = Path(__file__).resolve().parent.parent
    total = 0

    for path in find_python_files(root):
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)

        problems = check_text(text)
        problems.extend(check_docstrings_and_hints(tree))
        problems.extend(check_unused_imports(tree))

        for line, message in sorted(problems):
            print(f"{path.relative_to(root)}:{line}: {message}")
        total += len(problems)

    if total:
        print(f"\n{total} problem(s) found.")
        return 1

    print("Style check passed: no problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
