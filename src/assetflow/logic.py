from abc import ABC, abstractmethod
from typing import Callable, Any


class Logic(ABC):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class FunctionLogic(Logic):

    def __init__(self, func: Callable[..., Any]):
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)
