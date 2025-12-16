from abc import abstractmethod, ABC
from typing import Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .asset import Asset  # pragma: no cover # noqa: F401

from .dumper import Dumper


class DumperFactory(ABC):

    @abstractmethod
    def build(self, **logic_inputs: Mapping[str, "Asset"]) -> Dumper:
        raise NotImplementedError


__all__ = [
    DumperFactory
]
