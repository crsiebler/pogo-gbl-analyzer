from __future__ import annotations
from typing import List, Optional, Tuple
from ..models import RankingDataset, RankingRecord


class WinnersLosersProcessor:
    """Compute biggest winners and losers based on score deltas.

    Simplified parameters:
    analyze_top_n: limit LOSERS consideration to top N of NEW snapshot (by score). Winners always consider the full dataset.
    output_top_n: number of winners and losers to display (each). If None, show all.
      min_abs_delta: minimum absolute delta to keep.
    """

    def __init__(
        self,
        analyze_top_n: Optional[int] = None,
        output_top_n: Optional[int] = 25,
        min_abs_delta: float = 0.1,
    ):
        self.analyze_top_n = analyze_top_n
        self.output_top_n = output_top_n
        self.min_abs_delta = min_abs_delta

    def process(self, old: RankingDataset, new: RankingDataset) -> str:
        # Loser scope: top N of OLD snapshot (so large drops remain eligible)
        sorted_old: List[RankingRecord] = sorted(
            old.records.values(), key=lambda r: r.score, reverse=True
        )
        loser_scope_keys = {
            r.name_key
            for r in (
                sorted_old[: self.analyze_top_n] if self.analyze_top_n else sorted_old
            )
        }

        deltas_all: List[Tuple[str, float, float, float]] = []  # (key, old, new, delta)
        for key, new_rec in new.records.items():
            old_rec = old.get(key)
            if not new_rec or not old_rec:
                continue
            delta = new_rec.score - old_rec.score
            if abs(delta) >= self.min_abs_delta:
                deltas_all.append((key, old_rec.score, new_rec.score, delta))

        # Separate winners and losers with respective sorting
        winners = [d for d in deltas_all if d[3] > 0]
        losers = [d for d in deltas_all if d[3] < 0 and d[0] in loser_scope_keys]
        winners.sort(key=lambda x: x[3], reverse=True)  # biggest positive first
        losers.sort(key=lambda x: x[3])  # most negative (largest drop) first

        full_winner_count = len(winners)
        full_loser_count = len(losers)
        if self.output_top_n is not None:
            winners = winners[: self.output_top_n]
            losers = losers[: self.output_top_n]

        lines: List[str] = [
            f"League: {new.league}",
            f"Total comparable records: {len(deltas_all)}",
            f"Min abs delta filter: {self.min_abs_delta:.2f}",
        ]
        if self.analyze_top_n is not None:
            lines.append(
                f"Losers baseline: old top {self.analyze_top_n} (candidates: {len(loser_scope_keys)})"
            )
        else:
            lines.append("Losers scope: all records")
        lines.append("")
        lines.append(
            "Winners (Score Increase)"
            + (
                " (truncated)"
                if self.output_top_n and full_winner_count > len(winners)
                else ""
            )
        )
        for name, old_score, new_score, delta in winners:
            lines.append(
                f"+{delta:5.2f} {name} (old {old_score:.1f} -> new {new_score:.1f})"
            )
        lines.append("")
        lines.append(
            "Losers (Score Decrease)"
            + (
                " (truncated)"
                if self.output_top_n and full_loser_count > len(losers)
                else ""
            )
        )
        for name, old_score, new_score, delta in losers:
            lines.append(
                f"{delta:5.2f} {name} (old {old_score:.1f} -> new {new_score:.1f})"
            )
        return "\n".join(lines)
