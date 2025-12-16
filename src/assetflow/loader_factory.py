from abc import abstractmethod, ABC
from typing import Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .asset import Asset  # pragma: no cover # noqa: F401

from .loader import Loader


class LoaderFactory(ABC):

    @abstractmethod
    def build(self, **logic_inputs: Mapping[str, "Asset"]) -> Loader:
        raise NotImplementedError


__all__ = [
    LoaderFactory
]
