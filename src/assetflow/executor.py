from abc import ABC, abstractmethod
from typing import Callable, Sequence


class Executor(ABC):

    @abstractmethod
    def execute(self, tasks: Sequence[Callable[[], None]]) -> None:
        raise NotImplementedError


__all__ = [
    Executor
]
