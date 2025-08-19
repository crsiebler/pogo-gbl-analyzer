from __future__ import annotations
from typing import List, Optional, Tuple
from ..models import RankingDataset, RankingRecord


class WinnersLosersProcessor:
    """Compute biggest winners and losers based on score deltas.

    Simplified parameters:
      analyze_top_n: limit analysis to top N of NEW snapshot (by score). If None, use all.
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
        # Determine analysis subset (new snapshot top N if requested)
        if self.analyze_top_n is not None:
            considered_new: List[RankingRecord] = sorted(
                new.records.values(), key=lambda r: r.score, reverse=True
            )[: self.analyze_top_n]
            considered_keys = {r.name_key for r in considered_new}
        else:
            considered_new = list(new.records.values())
            considered_keys = set(new.records.keys())

        deltas: List[Tuple[str, float, float, float]] = []
        for key in considered_keys:
            new_rec = new.get(key)
            old_rec = old.get(key)
            if not new_rec or not old_rec:
                continue
            delta = new_rec.score - old_rec.score
            if abs(delta) >= self.min_abs_delta:
                deltas.append((key, old_rec.score, new_rec.score, delta))

        deltas.sort(key=lambda x: x[3], reverse=True)
        winners = deltas
        losers = list(reversed(deltas))
        if self.output_top_n is not None:
            winners = winners[: self.output_top_n]
            losers = losers[: self.output_top_n]

        lines: List[str] = [
            f"League: {new.league}",
            f"Analyzed records (new snapshot): {len(considered_keys)}",
            f"Eligible deltas >= {self.min_abs_delta:.2f}: {len(deltas)}",
        ]
        scope_note = (
            f"Top {self.analyze_top_n} new scores"
            if self.analyze_top_n is not None
            else "All records"
        )
        lines.append(f"Scope: {scope_note}")
        lines.append("")
        lines.append(
            f"Winners (Score Increase){' (truncated)' if self.output_top_n is not None and len(deltas) > len(winners) else ''}"
        )
        for name, old_score, new_score, delta in winners:
            lines.append(
                f"+{delta:5.2f} {name} (old {old_score:.1f} -> new {new_score:.1f})"
            )
        lines.append("")
        lines.append(
            f"Losers (Score Decrease){' (truncated)' if self.output_top_n is not None and len(deltas) > len(losers) else ''}"
        )
        for name, old_score, new_score, delta in losers:
            lines.append(
                f"{delta:5.2f} {name} (old {old_score:.1f} -> new {new_score:.1f})"
            )

        return "\n".join(lines)
