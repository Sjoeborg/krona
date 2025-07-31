from abc import ABC, abstractmethod
from typing import Any


class BaseStrategy(ABC):
    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        pass
