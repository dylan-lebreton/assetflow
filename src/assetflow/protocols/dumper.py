# assetflow/protocols/dumper.py
"""
Definition of Dumper and DumperFactory protocols.
"""

from typing import runtime_checkable, Protocol, Any, TypeVar

U = TypeVar("U", contravariant=True)


@runtime_checkable
class Dumper(Protocol[U]):
    """
    Protocol defining the interface for objects that can dump a value.

    A conforming object provides an operation:

        dump(obj: U) -> None

    which persists or otherwise handles a value of type ``U``. The protocol
    does not impose any constraints on the underlying storage mechanism
    or serialization format.

    Structural conformance may be validated at runtime using
    ``isinstance(obj, Dumper)``.
    """

    def dump(self, obj: U) -> None:  # pragma: no cover - interface
        """
        Persist or handle the given value.

        The concrete semantics of the dump operation are left to the
        implementing object.
        """
        ...


@runtime_checkable
class DumperFactory(Protocol):
    """
    Protocol for objects that produce Dumper instances.

    A conforming object implements:

        __call__(*args, **kwargs) -> Dumper[Any]

    allowing Dumper creation to depend on external parameters or
    computation context. The protocol does not prescribe how Dumper
    instances are configured or what they represent.

    Structural conformance may be validated at runtime using
    ``isinstance(obj, DumperFactory)``.
    """

    def __call__(self, *args: Any, **kwargs: Any) -> Dumper[Any]:  # pragma: no cover - interface
        ...
