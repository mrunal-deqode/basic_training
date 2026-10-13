#!/usr/bin/env bash
# Audit: does the code touch every item of the Module 1-5 checklist?
# Run from the project root:  bash tools/audit_checklist.sh

cd "$(dirname "$0")/.." || exit 1

audit() {
    # $1 = the checklist item, $2 = a pattern that proves it is used
    local files
    files=$(grep -lE "$2" src/*.py main.py | tr '\n' ' ')
    printf '%-34s %s\n' "$1" "${files:-*** MISSING ***}"
}

echo "== Module 1: Foundations"
audit "string methods" '\.(strip|lower|partition|isdigit)\('
audit "string indexing / slicing" 'cleaned\['
audit "booleans and None" 'is not None'
audit "arithmetic operators" ' / total'
audit "bitwise operators" ' << | & ~'
audit "input()" 'input\('
audit "f-strings" '[ (=]f"'
audit "if / elif / else" '^\s*elif '
audit "for loop" '^\s*for '
audit "while loop" '^\s*while '
audit "break" '^\s*break'
audit "continue" '^\s*continue'
audit "pass" '^\s*pass'
audit "range()" 'range\('

echo "== Module 2: Control flow and data structures"
audit "default arguments" ': bool = False'
audit "*args / **kwargs" '\*\*options|\*result_lists'
audit "scope (module-level state)" '^TIMINGS'
audit "lambda" 'lambda '
audit "map()" 'map\('
audit "filter()" 'filter\('
audit "reduce()" 'reduce\('
audit "recursion" 'collect_text\(inner'
audit "tuples" 'tuple\('
audit "sets" 'set\('
audit "list comprehension" '\[[^]]* for '
audit "dict comprehension" 'heading\.lower\(\): number'
audit "set comprehension" '\{[a-z]+ for '
audit "nested comprehension" 'for topic, keywords in topics'

echo "== Module 3: Modules and I/O"
audit "modules and packages" '^from src\.'
audit "context manager (with open)" '^\s*with open\('
audit "pathlib" 'from pathlib import'
audit "csv module" '^import csv'
audit "json module" '^import json'
audit "str.format()" '\.format\('

echo "== Module 4: Errors and classes"
audit "__init__ and self" 'def __init__'
audit "class attributes" '^    [A-Z_]+ = '
audit "@classmethod" '@classmethod'
audit "@staticmethod" '@staticmethod'
audit "inheritance and super()" 'super\(\)\.__init__'
audit "__eq__" 'def __eq__'
audit "__str__" 'def __str__'
audit "__repr__" 'def __repr__'
audit "try / except" '^\s*except '
audit "finally" '^\s*finally:'
audit "custom exceptions" '\(BriefCheckerError\)'
audit "iterator (__next__)" 'def __next__'
audit "generator (yield)" '^\s*yield'
audit "closure" 'return found'
audit "decorators" '^\s*@timed'

echo "== Module 5: Concurrency, testing and production"
# audit "concurrent.futures" 'concurrent\.futures'
audit "concurrent.futures" '^(from|import) concurrent'
audit "SQLite" 'import sqlite3'
audit "type hints" '\) -> '
audit "docstrings" '"""'
printf '%-34s %s\n' "unit tests (unittest)" \
    "$(grep -l 'import unittest' tests/*.py | tr '\n' ' ')"