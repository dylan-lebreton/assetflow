# assetflow/utils/checks.py
from __future__ import annotations

from collections.abc import Iterable as IterableABC, Mapping
from typing import Type, TypeVar

T = TypeVar("T")


def is_iterable_of(value: object, iface: Type[T]) -> bool:
    """
    Return True if `value` is an iterable (excluding strings, bytes, and mappings) and every element is an instance
    of `iface`.

    Notes
    -----
    - Generators and other one-shot iterables are materialized into a list to perform the check safely.
      This consumes the iterable.
    - An empty iterable returns True (vacuously true: "all elements" satisfy the predicate).
    - Strings, bytes, and mappings (e.g., dict) are explicitly excluded to avoid treating them as generic sequences.

    Parameters
    ----------
    value : object
        The object to test.
    iface : Type[T]
        The interface/protocol/class that all elements must implement.

    Returns
    -------
    bool
        True iff `value` is a non-string, non-bytes, non-mapping iterable whose elements are all instances of `iface`.

    Examples
    --------
    >>> from typing import runtime_checkable, Protocol
    >>> @runtime_checkable
    ... class Writer(Protocol):
    ...     def write(self, obj) -> None: ...
    ...
    >>> class FileWriter:
    ...     def write(self, obj) -> None: pass
    ...
    >>> is_iterable_of([FileWriter(), FileWriter()], Writer)
    True
    >>> is_iterable_of([FileWriter(), object()], Writer)
    False
    >>> is_iterable_of("not considered iterable here", Writer)
    False
    """
    # Reject non-iterables and common non-target iterables (str/bytes/mappings).
    if not (isinstance(value, IterableABC) and not isinstance(value, (str, bytes, Mapping))):
        return False

    # Materialize to safely validate generators/iterators and avoid double iteration.
    seq = list(value)

    # Vacuously true for empty iterables.
    if not seq:
        return True

    # All elements must be instances of `iface`. Supports runtime_checkable Protocols.
    return all(isinstance(obj, iface) for obj in seq)
