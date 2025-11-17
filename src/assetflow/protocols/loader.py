# assetflow/protocols/loader.py
"""
Definition of Loader and LoaderFactory protocols.
"""

from typing import runtime_checkable, Protocol, Any, TypeVar

T = TypeVar("T", covariant=True)


@runtime_checkable
class Loader(Protocol[T]):
    """
    Protocol defining the interface for objects that can load a value.

    A conforming object provides a parameterless method:

        load() -> T

    which returns a value of type ``T``.  The protocol does not impose any
    constraints on the underlying retrieval mechanism or storage model.

    Structural conformance may be validated at runtime using
    ``isinstance(obj, Loader)``.
    """

    def load(self) -> T:  # pragma: no cover - interface
        """
        Return the loaded value.

        The concrete semantics of the retrieval process are left to the
        implementing object.
        """
        ...


@runtime_checkable
class LoaderFactory(Protocol):
    """
    Protocol for objects that produce Loader instances.

    A conforming object implements:

        __call__(*args, **kwargs) -> Loader[Any]

    allowing Loader creation to depend on external parameters or
    computation context.  The protocol does not prescribe how Loader
    instances are configured or what they represent.

    Structural conformance may be validated at runtime using
    ``isinstance(obj, LoaderFactory)``.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Loader[Any]:  # pragma: no cover - interface
        ...
