class BriefCheckerError(Exception):
    pass

class MissingFileError(BriefCheckerError):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        super().__init__(f"Input file not found: {file_path}")


class EmptyInputError(BriefCheckerError):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        super().__init__(f"Input file is empty: {file_path}")


class MalformedRowError(BriefCheckerError):
    def __init__(self, detail: str, location: str = "file") -> None:
        self.detail = detail
        self.location = location
        super().__init__(f"Malformed data in {location}: {detail}")


class InvalidDataTypeError(BriefCheckerError):
    def __init__(self, field_name: str, expected: str, actual_value: object) -> None:
        self.field_name = field_name
        self.expected = expected
        self.actual = type(actual_value).__name__
        super().__init__(
            f"Field '{field_name}' should be {expected}, "
            f"but got {self.actual}"
        )


class MissingSectionError(BriefCheckerError):
    def __init__(self, section_name: str) -> None:
        self.section_name = section_name
        super().__init__(f"Required section is missing: {section_name}")