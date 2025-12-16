from abc import ABC, abstractmethod
from typing import Any


class Dumper(ABC):

    @abstractmethod
    def dump(self, obj: Any) -> None:
        raise NotImplementedError


__all__ = [
    Dumper
]
