from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Protocol, Tuple


@dataclass(frozen=True)
class RankingRecord:
    pokemon: str
    score: float
    # Keep raw row for potential future processors
    raw: Dict[str, str]

    @property
    def name_key(self) -> str:
        """Return a normalized key to match between datasets.
        Currently uses the exact pokemon string; adjust here if needed later.
        """
        return self.pokemon


@dataclass
class RankingDataset:
    league: str  # great | ultra | master
    records: Dict[str, RankingRecord]  # keyed by name_key

    def get(self, key: str) -> Optional[RankingRecord]:
        return self.records.get(key)


class RankingsLoader:
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


class BaseRankingProcessor(Protocol):
    def process(self, old: RankingDataset, new: RankingDataset) -> str:
        """Return a human-readable report string."""
        ...


class WinnersLosersProcessor:
    def __init__(
        self,
        top_n: int = 25,
        min_abs_delta: float = 0.1,
        old_top_n_filter: Optional[int] = None,
        include_outside_meta_winners: bool = False,
    ):
        self.top_n = top_n
        self.min_abs_delta = min_abs_delta
        self.old_top_n_filter = old_top_n_filter
        self.include_outside_meta_winners = include_outside_meta_winners

    def process(self, old: RankingDataset, new: RankingDataset) -> str:
        allowed: Optional[set[str]] = None
        old_sorted: List[RankingRecord] = []
        if self.old_top_n_filter:
            old_sorted = sorted(
                old.records.values(), key=lambda r: r.score, reverse=True
            )[: self.old_top_n_filter]
            allowed = {r.name_key for r in old_sorted}
        min_meta_score = min((r.score for r in old_sorted), default=0.0)

        deltas: List[Tuple[str, float, float, float]] = (
            []
        )  # within meta (or unrestricted)
        emerging: List[Tuple[str, Optional[float], float, float]] = (
            []
        )  # outside old meta but now relevant

        for name, new_rec in new.records.items():
            old_rec = old.get(name)
            if not old_rec:
                # brand new entry
                if self.include_outside_meta_winners and allowed is not None:
                    if new_rec.score >= min_meta_score and new_rec.score > 0:
                        emerging.append((name, None, new_rec.score, new_rec.score))
                continue
            delta = new_rec.score - old_rec.score
            if allowed is not None and name not in allowed:
                # Potential emerging winner
                if (
                    self.include_outside_meta_winners
                    and delta > 0
                    and new_rec.score >= min_meta_score
                    and delta >= self.min_abs_delta
                ):
                    emerging.append((name, old_rec.score, new_rec.score, delta))
                continue
            if abs(delta) >= self.min_abs_delta:
                deltas.append((name, old_rec.score, new_rec.score, delta))

        deltas.sort(key=lambda x: x[3], reverse=True)
        winners = deltas[: self.top_n]
        losers = sorted(deltas, key=lambda x: x[3])[: self.top_n]

        lines = [
            f"League: {new.league}",
            f"Total compared (primary set): {len(deltas)}",
        ]
        if allowed is not None:
            lines.append(
                f"(Restricted to top {self.old_top_n_filter} from old dataset)"
            )
            if self.include_outside_meta_winners:
                lines.append(
                    f"Including emerging winners outside previous meta (threshold score >= {min_meta_score:.1f})"
                )
        lines.extend(["", f"Top {len(winners)} Winners (Score Increase)"])
        for name, old_score, new_score, delta in winners:
            lines.append(
                f"+{delta:5.2f} {name} (old {old_score:.1f} -> new {new_score:.1f})"
            )
        lines.append("")
        lines.append(f"Top {len(losers)} Losers (Score Decrease)")
        for name, old_score, new_score, delta in losers:
            lines.append(
                f"{delta:5.2f} {name} (old {old_score:.1f} -> new {new_score:.1f})"
            )

        if allowed is None:
            new_only = [n for n in new.records if n not in old.records]
            removed = [n for n in old.records if n not in new.records]
            if new_only:
                lines.append("")
                lines.append(
                    f"New entries ({len(new_only)}): {', '.join(sorted(new_only)[:30])}{'...' if len(new_only) > 30 else ''}"
                )
            if removed:
                lines.append("")
                lines.append(
                    f"Removed entries ({len(removed)}): {', '.join(sorted(removed)[:30])}{'...' if len(removed) > 30 else ''}"
                )
        else:
            if self.include_outside_meta_winners and emerging:
                emerging.sort(key=lambda x: x[3], reverse=True)
                lines.append("")
                lines.append(
                    f"Emerging Winners Outside Previous Meta (top {min(self.top_n, len(emerging))})"
                )
                for name, old_score, new_score, delta in emerging[: self.top_n]:
                    if old_score is None:
                        lines.append(f"NEW +{delta:5.2f} {name} (new {new_score:.1f})")
                    else:
                        lines.append(
                            f"+{delta:5.2f} {name} (old {old_score:.1f} -> new {new_score:.1f})"
                        )

        return "\n".join(lines)
