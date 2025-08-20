from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class RankingRecord:
    """Represents a single Pokémon ranking row.

    rank: 1-based position derived from CSV order (lower is better). Not persisted in raw.
    """

    pokemon: str
    score: float
    rank: int
    raw: Dict[str, str]

    @property
    def name_key(self) -> str:
        return self.pokemon


@dataclass
class RankingDataset:
    """Collection of ranking records for a league."""

    league: str
    records: Dict[str, RankingRecord]

    def get(self, key: str) -> Optional[RankingRecord]:
        return self.records.get(key)
