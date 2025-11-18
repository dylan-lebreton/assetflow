# assetflow/protocols/combiner.py
"""
Definition of the Combiner protocol and the Combination type.
"""

from typing import runtime_checkable, Protocol, Iterable, TYPE_CHECKING, Dict, Union

if TYPE_CHECKING:  # pragma: no cover
    from ..asset import Asset  # noqa: F401

# A Combination describes, for a single logical evaluation, how
# upstream assets are grouped per parameter name. Each value can be
# a single Asset (e.g. unpartitioned) or an iterable of Assets
# (e.g. grouping multiple partitions together).
Combination = Dict[str, Union["Asset", Iterable["Asset"]]]


@runtime_checkable
class Combiner(Protocol):
    """
    Protocol defining the interface for dependency combiners.

    A Combiner receives the upstream assets of a computed asset as
    keyword arguments (one keyword per logical parameter name) and
    yields an iterable of ``Combination`` objects. Each ``Combination``
    describes how upstream assets (or their partitions / sub-assets)
    should be grouped when invoking the computation logic.

    The protocol is intentionally minimal and purely structural:
    any callable with a compatible ``__call__`` signature conforms.

    Structural conformance may be validated at runtime using
    ``isinstance(obj, Combiner)``.
    """

    def __call__(self, **dependencies: "Asset") -> Iterable[Combination]:  # pragma: no cover - interface
        """
        Yield combinations of upstream assets.

        Parameters
        ----------
        **dependencies :
            Mapping from logical parameter name to upstream ``Asset``.
            The concrete structure of each asset (partitioned or not)
            is left to higher-level components.

        Returns
        -------
        Iterable[Combination]
            An iterable of combination descriptors to be consumed by
            the computation layer.
        """
        ...
