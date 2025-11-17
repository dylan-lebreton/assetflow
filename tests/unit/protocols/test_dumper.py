# tests/unit/protocols/test_dumper.py
from pathlib import Path

import pytest

from assetflow.protocols.dumper import Dumper


class FileDumper:
    """Minimal dumper writing to a file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def dump(self, obj) -> None:
        self.path.write_text(str(obj))


@pytest.mark.unit
def test_file_dumper_writes_to_file(tmp_path: Path):
    """Dumper should persist the given object to disk."""
    file = tmp_path / "out.txt"
    dumper = FileDumper(file)

    dumper.dump("hello dumper")

    assert file.read_text() == "hello dumper"


@pytest.mark.unit
def test_file_dumper_is_instance_of_protocol(tmp_path: Path):
    """FileDumper should be recognized as a Dumper at runtime."""
    file = tmp_path / "out.txt"
    dumper = FileDumper(file)

    assert isinstance(dumper, Dumper)
