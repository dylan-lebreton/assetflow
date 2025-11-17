# tests/unit/protocols/test_loader.py
from pathlib import Path

import pytest

from src.protocols.loader import Loader


class FileLoader:
    """Minimal loader reading from a file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> str:
        return self.path.read_text()


@pytest.mark.unit
def test_file_loader_reads_from_file(tmp_path: Path) -> None:
    """Loader should retrieve the value previously written to disk."""
    file = tmp_path / "in.txt"
    file.write_text("hello loader")  # pre-create content

    loader = FileLoader(file)

    assert loader.load() == "hello loader"


@pytest.mark.unit
def test_file_loader_is_instance_of_protocol(tmp_path: Path) -> None:
    """FileLoader should be recognized as a Loader at runtime."""
    file = tmp_path / "in.txt"
    file.write_text("data")

    loader = FileLoader(file)

    assert isinstance(loader, Loader)
