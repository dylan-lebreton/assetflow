from __future__ import annotations

import pytest
from typing import Protocol, runtime_checkable

from assetflow.utils.checks import is_iterable_of


@runtime_checkable
class Writer(Protocol):
    def write(self, obj) -> None: ...


class FileWriter:
    def write(self, obj) -> None:
        pass


class NoWriter:
    pass


@pytest.mark.unit
def test_non_iterable_returns_false() -> None:
    assert is_iterable_of(123, int) is False
    assert is_iterable_of(None, object) is False


@pytest.mark.unit
def test_strings_and_bytes_are_excluded() -> None:
    assert is_iterable_of("abc", str) is False
    assert is_iterable_of(b"abc", bytes) is False


@pytest.mark.unit
def test_mappings_are_excluded() -> None:
    assert is_iterable_of({"a": 1}, int) is False


@pytest.mark.unit
def test_empty_iterables_return_true() -> None:
    assert is_iterable_of([], int) is True
    assert is_iterable_of(tuple(), int) is True
    assert is_iterable_of((x for x in ()), int) is True


@pytest.mark.unit
def test_list_of_concrete_type() -> None:
    assert is_iterable_of([1, 2, 3], int) is True
    assert is_iterable_of([1, "x", 3], int) is False


@pytest.mark.unit
def test_tuple_and_set() -> None:
    assert is_iterable_of((1, 2, 3), int) is True
    assert is_iterable_of({1, 2, 3}, int) is True
    assert is_iterable_of({1, "x", 3}, int) is False


@pytest.mark.unit
def test_protocol_positive() -> None:
    assert is_iterable_of([FileWriter(), FileWriter()], Writer) is True


@pytest.mark.unit
def test_protocol_negative_member_missing() -> None:
    assert is_iterable_of([FileWriter(), NoWriter()], Writer) is False


@pytest.mark.unit
def test_generator_consumption_note() -> None:
    def gen():
        yield FileWriter()
        yield FileWriter()

    g = gen()
    assert is_iterable_of(g, Writer) is True
    assert list(g) == []
