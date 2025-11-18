# tests/unit/protocols/test_combiner.py
from typing import Iterable

import pytest

from assetflow.protocols.combiner import Combiner, Combination


class DummyAsset:
    """Minimal stand-in for an Asset."""
    pass


@pytest.mark.unit
def test_function_is_instance_of_combiner_protocol() -> None:
    """A plain callable with the right shape should be a Combiner at runtime."""

    # noinspection PyUnusedLocal
    def combine(**dependencies: DummyAsset) -> Iterable[Combination]:
        # Return a single empty combination just to satisfy the shape
        yield {}

    assert isinstance(combine, Combiner)


@pytest.mark.unit
def test_class_with_call_is_instance_of_combiner_protocol() -> None:
    """A class implementing __call__ is a Combiner at runtime."""

    class SimpleCombiner:
        def __call__(self, **dependencies: DummyAsset) -> Iterable[Combination]:
            # Return a single empty combination just to satisfy the shape
            yield {}

    c = SimpleCombiner()
    assert isinstance(c, Combiner)
