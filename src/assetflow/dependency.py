# src/assetflow/dependency.py
from typing import Generic, TypeVar

T = TypeVar("T")
A = TypeVar("A")


class Dependency(Generic[T, A]):
    ...
