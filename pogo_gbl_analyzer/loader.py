from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict
from .models import RankingRecord, RankingDataset


class RankingsLoader:
    """Load ranking CSV exports into in-memory datasets."""

    REQUIRED_COLUMNS = {"Pokemon", "Score"}

    def load_csv(self, path: str | Path, league: str) -> RankingDataset:
        path = Path(path)
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            missing = self.REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"Missing required columns {missing} in {path}")
            records: Dict[str, RankingRecord] = {}
            for row in reader:
                try:
                    score = float(row["Score"]) if row.get("Score") else 0.0
                except ValueError:
                    continue
                pokemon = row["Pokemon"].strip()
                rec = RankingRecord(pokemon=pokemon, score=score, raw=row)
                records[rec.name_key] = rec
        return RankingDataset(league=league, records=records)
