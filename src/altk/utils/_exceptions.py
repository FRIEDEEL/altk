"""Common exceptions for all sublibraries.
"""


class DataFileInvalid(BaseException):
    """Exception when the file can be found, but with invalid format.

    """
    def __init__(self, *args: object) -> None:
        super().__init__(*args)