from __future__ import annotations
from typing import List, Optional, Tuple
from ..models import RankingDataset, RankingRecord


class RankShiftProcessor:
    """Compute biggest climbs and drops based on rank changes (position shift).

    Lower rank value means a better position (rank 1 is best). A *drop* means the
    rank number increased (e.g., 5 -> 18). A *climb* means the rank number decreased (e.g., 42 -> 17).

    analyze_top_n: restrict LOSER consideration to Pokémon that were within the top N of the OLD snapshot
                   (mirrors losers scoping in WinnersLosersProcessor so large falls are still eligible).
    output_top_n: number of climbers and droppers to show.
    min_rank_delta: minimum absolute rank shift to include (default 1 = any change).
    """

    def __init__(
        self,
        analyze_top_n: Optional[int] = None,
        output_top_n: Optional[int] = 25,
        min_rank_delta: int = 1,
    ) -> None:
        self.analyze_top_n = analyze_top_n
        self.output_top_n = output_top_n
        self.min_rank_delta = min_rank_delta

    def process(self, old: RankingDataset, new: RankingDataset) -> str:
        # Build loser scope (candidates for tracking large drops) from OLD snapshot top N ranks.
        sorted_old: List[RankingRecord] = sorted(
            old.records.values(), key=lambda r: r.rank
        )
        loser_scope_keys = {
            r.name_key
            for r in (
                sorted_old[: self.analyze_top_n] if self.analyze_top_n else sorted_old
            )
        }

        shifts: List[Tuple[str, int, int, int]] = (
            []
        )  # key, old_rank, new_rank, delta (old - new)
        for key, new_rec in new.records.items():
            old_rec = old.get(key)
            if not old_rec:
                continue
            # delta_rank positive means improved (moved up); negative means fell.
            delta_rank = old_rec.rank - new_rec.rank
            if abs(delta_rank) >= self.min_rank_delta:
                shifts.append((key, old_rec.rank, new_rec.rank, delta_rank))

        climbers = [s for s in shifts if s[3] > 0]  # improved rank (lower number)
        droppers = [s for s in shifts if s[3] < 0 and s[0] in loser_scope_keys]
        climbers.sort(key=lambda x: x[3], reverse=True)  # biggest improvement first
        droppers.sort(key=lambda x: x[3])  # most negative (largest fall) first

        full_climb_count = len(climbers)
        full_drop_count = len(droppers)
        if self.output_top_n is not None:
            climbers = climbers[: self.output_top_n]
            droppers = droppers[: self.output_top_n]

        lines: List[str] = [
            f"League: {new.league}",
            f"Total comparable records: {len(shifts)}",
            f"Min rank shift filter: {self.min_rank_delta}",
        ]
        if self.analyze_top_n is not None:
            lines.append(
                f"Drop scope baseline: old top {self.analyze_top_n} (candidates: {len(loser_scope_keys)})"
            )
        else:
            lines.append("Drop scope: all records")
        lines.append("")
        lines.append(
            "Climbers (Rank Improvements)"
            + (
                " (truncated)"
                if self.output_top_n and full_climb_count > len(climbers)
                else ""
            )
        )
        for name, old_rank, new_rank, delta in climbers:
            lines.append(
                f"+{delta:3d} {name} (old rank {old_rank} -> new rank {new_rank})"
            )
        lines.append("")
        lines.append(
            "Droppers (Rank Falls)"
            + (
                " (truncated)"
                if self.output_top_n and full_drop_count > len(droppers)
                else ""
            )
        )
        for name, old_rank, new_rank, delta in droppers:
            # delta is negative
            lines.append(
                f"{delta:4d} {name} (old rank {old_rank} -> new rank {new_rank})"
            )
        return "\n".join(lines)
