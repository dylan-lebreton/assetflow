# tests/unit/protocols/test_dumper_factory.py
from pathlib import Path
from typing import Any, Iterable

import pytest

from assetflow.protocols.dumper import Dumper, DumperFactory


class FileDumper:
    """Minimal dumper writing to a file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def dump(self, obj) -> None:
        self.path.write_text(str(obj))


@pytest.mark.unit
def test_function_factory_produces_working_dumper(tmp_path: Path) -> None:
    """A callable factory should create a Dumper that writes to the expected path."""

    # function-based factory that targets base_dir / "<name>.txt"
    def file_dumper_factory(base_dir: Path):
        def make(name: str) -> Dumper[Any]:
            return FileDumper(base_dir / f"{name}.txt")

        return make

    factory = file_dumper_factory(tmp_path)
    dumper = factory("result_01")

    # it should behave like a Dumper
    assert isinstance(dumper, Dumper)

    # and actually write to disk
    dumper.dump("hello")
    assert (tmp_path / "result_01.txt").read_text() == "hello"


@pytest.mark.unit
def test_function_factory_is_instance_of_protocol(tmp_path: Path) -> None:
    """A plain function that matches the callable shape is a DumperFactory at runtime."""

    def make_dumper(name: str) -> Dumper[Any]:
        return FileDumper(tmp_path / f"{name}.txt")

    assert isinstance(make_dumper, DumperFactory)


@pytest.mark.unit
def test_class_based_factory_is_instance_and_works(tmp_path: Path) -> None:
    class FileDumperFactory:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def __call__(self, name: str) -> Dumper[Any]:
            return FileDumper(self.base_dir / f"{name}.txt")

    factory = FileDumperFactory(tmp_path)
    assert isinstance(factory, DumperFactory)

    d = factory("foo")
    d.dump("bar")
    assert (tmp_path / "foo.txt").read_text() == "bar"


@pytest.mark.unit
def test_iterable_of_dumpers_is_not_a_factory(tmp_path: Path) -> None:
    """A plain iterable of Dumper instances must NOT be mistaken for a DumperFactory."""
    d1 = FileDumper(tmp_path / "a.txt")
    d2 = FileDumper(tmp_path / "b.txt")
    dumpers: Iterable[Dumper[Any]] = [d1, d2]

    # The iterable itself is not a Dumper nor a DumperFactory
    assert not isinstance(dumpers, Dumper)
    assert not isinstance(dumpers, DumperFactory)

    # But each element is a Dumper
    for d in dumpers:
        assert isinstance(d, Dumper)


@pytest.mark.unit
def test_bad_factory_shape_note(tmp_path: Path) -> None:
    """
    NOTE: Any callable matches DumperFactory structurally at runtime.
    Return type isn't checked by isinstance; your build function should validate it.
    """

    # noinspection PyUnusedLocal
    # A callable that returns the WRONG thing (an int) still counts as 'callable'
    def bad_factory(name: str) -> int:  # wrong return type on purpose
        return 42

    # Because DumperFactory is structural + runtime_checkable, this is True:
    assert isinstance(bad_factory, DumperFactory)

    # And that's OK: your higher-level dispatcher (e.g., build_items_from_combinations)
    # already checks that the factory's return value is actually a Dumper and raises otherwise.
