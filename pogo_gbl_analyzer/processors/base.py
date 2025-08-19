from __future__ import annotations
from typing import Protocol
from ..models import RankingDataset


class BaseRankingProcessor(Protocol):
    """Protocol for ranking processors returning a human-readable report."""

    def process(
        self, old: RankingDataset, new: RankingDataset
    ) -> str:  # pragma: no cover
        ...
