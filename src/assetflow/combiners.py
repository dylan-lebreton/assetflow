from typing import Iterable, TYPE_CHECKING, Mapping

from .combiner import Combiner

if TYPE_CHECKING:
    from .asset import Asset  # pragma: no cover # noqa: F401


class GatherCombiner(Combiner):

    def combine(self, **dependencies: "Asset") -> Iterable[Mapping[str, "Asset"]]:
        ...
        # À définir
