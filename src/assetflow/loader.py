from abc import abstractmethod, ABC
from typing import Any


class Loader(ABC):

    @abstractmethod
    def load(self) -> Any:
        raise NotImplementedError


__all__ = [
    Loader
]
