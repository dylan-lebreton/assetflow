from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable, Mapping

if TYPE_CHECKING:
    from .asset import Asset  # pragma: no cover # noqa: F401


class Combiner(ABC):

    @abstractmethod
    def combine(self, **dependencies: "Asset") -> Iterable[Mapping[str, "Asset"]]:
        raise NotImplementedError
