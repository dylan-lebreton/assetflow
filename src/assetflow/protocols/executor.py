# assetflow/protocols/executor.py
"""
Definition of the Executor protocol.
"""

from typing import runtime_checkable, Protocol, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..asset import Asset  # noqa: F401


@runtime_checkable
class Executor(Protocol):
    """
    Protocol defining the interface for execution strategies.

    An Executor receives a sequence of assets that are ready to be
    computed and is responsible for driving their execution. The
    protocol does not prescribe how scheduling is implemented;
    implementations may run assets sequentially, concurrently in
    threads, in separate processes, or delegate to an external
    scheduler.

    The protocol is purely structural: any callable with a compatible
    ``__call__`` signature is considered an Executor.

    Structural conformance may be validated at runtime using
    ``isinstance(obj, Executor)``.
    """

    def __call__(self, assets: Sequence["Asset"]) -> None:  # pragma: no cover - interface
        """
        Execute the given assets.

        Parameters
        ----------
        assets :
            Sequence of assets that should be computed. The concrete
            execution behavior (order, concurrency, error handling)
            is determined by the implementing object.
        """
        ...
