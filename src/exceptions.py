"""Custom exceptions for the Blueprint Compliance Checker.

Every exception inherits from BriefCheckerError, so calling code can
catch all of this project's errors with a single except clause.
"""


class BriefCheckerError(Exception):
    """Base class for every error raised by this project."""


class MissingFileError(BriefCheckerError):
    """Raised when the input file does not exist."""

    def __init__(self, file_path: str) -> None:
        """Remember the path and build the error message."""
        # Keep the path on the object so other code (and tests) can read it.
        self.file_path = file_path
        # super().__init__ sets the message that is shown to the user.
        super().__init__(f"Input file not found: {file_path}")


class EmptyInputError(BriefCheckerError):
    """Raised when the input file exists but contains no data."""

    def __init__(self, file_path: str) -> None:
        """Remember the path and build the error message."""
        self.file_path = file_path
        super().__init__(f"Input file is empty: {file_path}")


class MalformedRowError(BriefCheckerError):
    """Raised when the JSON text or one of its section entries is broken."""

    def __init__(self, detail: str, location: str = "file") -> None:
        """Remember what is wrong and where, and build the message."""
        # 'location' says where the problem is, e.g. "file" or "section 3".
        self.detail = detail
        self.location = location
        super().__init__(f"Malformed data in {location}: {detail}")


class InvalidDataTypeError(BriefCheckerError):
    """Raised when a value has a different type than the blueprint expects."""

    def __init__(
        self, field_name: str, expected: str, actual_value: object
    ) -> None:
        """Remember the field and both types, and build the message."""
        self.field_name = field_name
        self.expected = expected
        # type(x).__name__ gives a readable name such as 'str' or 'list'.
        self.actual = type(actual_value).__name__
        super().__init__(
            f"Field '{field_name}' should be {expected}, "
            f"but got {self.actual}"
        )


class MissingSectionError(BriefCheckerError):
    """Raised when a required section is not present in the brief."""

    def __init__(self, section_name: str) -> None:
        """Remember the section name and build the error message."""
        self.section_name = section_name
        super().__init__(f"Required section is missing: {section_name}")