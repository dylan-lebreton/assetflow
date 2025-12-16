from pathlib import Path
from typing import Sequence

import polars as pl

from assetflow import Loader


class CSVLoader(Loader):

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()

    def load(self) -> pl.LazyFrame:
        return pl.scan_csv(self.path)


class MultiCSVLoader(Sequence[Loader]):
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self._paths = list(self.path.iterdir())  # snapshot (stable)

    def __len__(self) -> int:
        return len(self._paths)

    def __getitem__(self, i: int) -> Loader:
        return CSVLoader(self._paths[i])
