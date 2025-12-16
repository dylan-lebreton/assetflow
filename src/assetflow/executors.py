from typing import Sequence, Callable

from .executor import Executor


class SequentialExecutor(Executor):
    def execute(self, tasks: Sequence[Callable[[], None]]) -> None:
        for task in tasks:
            task()
