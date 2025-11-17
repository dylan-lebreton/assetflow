# tests/unit/protocols/test_loader_factory.py
from pathlib import Path
from typing import Any, Iterable

import pytest

from src.protocols.loader import Loader, LoaderFactory


class FileLoader:
    """Minimal loader reading from a file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> str:
        return self.path.read_text()


@pytest.mark.unit
def test_function_factory_produces_working_loader(tmp_path: Path) -> None:
    """A callable factory should create a Loader that reads from the expected path."""

    # prepare a file with content
    (tmp_path / "result_01.txt").write_text("hello")

    def file_loader_factory(base_dir: Path):
        def make(name: str) -> Loader[Any]:
            return FileLoader(base_dir / f"{name}.txt")

        return make

    factory = file_loader_factory(tmp_path)
    loader = factory("result_01")

    assert isinstance(loader, Loader)
    assert loader.load() == "hello"


@pytest.mark.unit
def test_function_factory_is_instance_of_protocol(tmp_path: Path) -> None:
    """A plain function that matches the callable shape is a LoaderFactory at runtime."""

    def make_loader(name: str) -> Loader[Any]:
        return FileLoader(tmp_path / f"{name}.txt")

    assert isinstance(make_loader, LoaderFactory)


@pytest.mark.unit
def test_class_based_factory_is_instance_and_works(tmp_path: Path) -> None:
    """A class implementing __call__ should be recognized as a LoaderFactory."""

    class FileLoaderFactory:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def __call__(self, name: str) -> Loader[Any]:
            return FileLoader(self.base_dir / f"{name}.txt")

    # prepare a file
    (tmp_path / "foo.txt").write_text("bar")

    factory = FileLoaderFactory(tmp_path)
    assert isinstance(factory, LoaderFactory)

    loader = factory("foo")
    assert loader.load() == "bar"


@pytest.mark.unit
def test_iterable_of_loaders_is_not_a_factory(tmp_path: Path) -> None:
    """A plain iterable of Loader instances must NOT be mistaken for a LoaderFactory."""

    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.txt").write_text("B")

    l1 = FileLoader(tmp_path / "a.txt")
    l2 = FileLoader(tmp_path / "b.txt")
    loaders: Iterable[Loader[Any]] = [l1, l2]

    # The iterable itself is not a Loader nor a LoaderFactory
    assert not isinstance(loaders, Loader)
    assert not isinstance(loaders, LoaderFactory)

    # But each element is a Loader
    for l in loaders:
        assert isinstance(l, Loader)


@pytest.mark.unit
def test_bad_factory_shape_note() -> None:
    """
    NOTE: Any callable matches LoaderFactory structurally at runtime.
    Return type isn't checked by isinstance; higher-level code should validate it.
    """

    # noinspection PyUnusedLocal
    def bad_factory(name: str) -> int:  # wrong return type on purpose
        return 123

    assert isinstance(bad_factory, LoaderFactory)
