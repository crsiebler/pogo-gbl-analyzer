from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class RankingRecord:
    """Represents a single Pokémon ranking row."""

    pokemon: str
    score: float
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
