# tests/unit/protocols/test_executor.py
from typing import Sequence

import pytest

from assetflow.protocols.executor import Executor


class DummyAsset:
    """Minimal asset with a compute method."""

    def __init__(self, name: str, sink: list[str]) -> None:
        self.name = name
        self.sink = sink

    def compute(self) -> None:
        self.sink.append(self.name)


@pytest.mark.unit
def test_function_is_instance_of_executor_protocol() -> None:
    """A plain callable with the right shape should be an Executor at runtime."""

    def run(assets: Sequence[DummyAsset]) -> None:
        for a in assets:
            a.compute()

    assert isinstance(run, Executor)


@pytest.mark.unit
def test_class_with_call_is_instance_of_executor_protocol() -> None:
    """A class implementing __call__ is an Executor at runtime."""

    class Runner:
        def __call__(self, assets: Sequence[DummyAsset]) -> None:
            for a in assets:
                a.compute()

    r = Runner()
    assert isinstance(r, Executor)


@pytest.mark.unit
def test_executor_invokes_compute_on_each_asset() -> None:
    """Executor-like callable should drive compute() on every asset."""
    sink: list[str] = []

    def run(assets_: Sequence[DummyAsset]) -> None:
        for a in assets_:
            a.compute()

    assets = [DummyAsset("a", sink), DummyAsset("b", sink)]

    # Sanity: recognized as an Executor
    assert isinstance(run, Executor)

    # And it actually calls compute() on each asset
    run(assets)

    assert sink == ["a", "b"]
