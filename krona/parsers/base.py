"""Abstract base class defining the interface for all parsers"""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from krona.models.transaction import Transaction


class BaseParser(ABC):
    @abstractmethod
    def parse_file(self, file_path: str) -> Iterator[Transaction]:
        """Parse a CSV file and yield Transaction objects."""
        pass

    @abstractmethod
    def validate_format(self, file_path: str) -> bool:
        """Return True if the file matches this parser's format."""
        pass

    def to_float(self, value: str) -> float:
        """Convert a string to a float, regardles of the decimal separator."""
        return float(value.replace(" ", "").replace(",", "."))
