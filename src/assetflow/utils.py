# assetflow/utils/checks.py

from __future__ import annotations

from collections.abc import Sequence
from typing import Type, TypeVar

T = TypeVar("T")


def is_sequence_of(value: object, iface: Type[T]) -> bool:
    """
    Return True if `value` is a non-string, non-bytes Sequence whose
    elements all implement `iface`.

    Notes
    -----
    - Strings and bytes are explicitly excluded.
    - An empty sequence returns True (vacuously true).

    Parameters
    ----------
    value : object
        Object to test.
    iface : type
        Type or protocol expected for each item.

    Returns
    -------
    bool
        True iff `value` is a sequence of objects implementing `iface`.
    """
    # Must be a Sequence but not string/bytes
    if not (isinstance(value, Sequence) and not isinstance(value, (str, bytes))):
        return False

    # Empty sequence OK
    if len(value) == 0:
        return True

    # Check element types
    return all(isinstance(elem, iface) for elem in value)
