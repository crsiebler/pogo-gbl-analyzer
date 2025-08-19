from __future__ import annotations
from typing import List, Optional
from ..models import RankingDataset, RankingRecord


class MoveSetChangesProcessor:
    """Report move set changes for top meta Pokémon.

    Considers top N (by new score). If a Pokémon exists in both datasets and
    any of its Fast or Charged moves differ, the change is listed.
    """

    FAST_FIELD = "Fast Move"
    CHARGED_FIELDS = ["Charged Move 1", "Charged Move 2"]

    def __init__(self, top_n: int = 50):
        self.top_n = top_n

    def _sorted(self, ds: RankingDataset) -> List[RankingRecord]:
        return sorted(ds.records.values(), key=lambda r: r.score, reverse=True)

    def process(self, old: RankingDataset, new: RankingDataset) -> str:
        top_new = self._sorted(new)[: self.top_n]
        lines: List[str] = [
            f"League: {new.league}",
            f"Move Set Changes Among Top {len(top_new)} (by new score)",
        ]

        change_count = 0
        for rec_new in top_new:
            rec_old: Optional[RankingRecord] = old.get(rec_new.name_key)
            if not rec_old:
                continue
            diffs: List[str] = []
            fast_old = rec_old.raw.get(self.FAST_FIELD, "").strip()
            fast_new = rec_new.raw.get(self.FAST_FIELD, "").strip()
            if fast_old and fast_new and fast_old != fast_new:
                diffs.append(f"Fast: {fast_old} -> {fast_new}")
            # Charged moves: order-insensitive comparison.
            old_charged = [rec_old.raw.get(f, "").strip() for f in self.CHARGED_FIELDS]
            new_charged = [rec_new.raw.get(f, "").strip() for f in self.CHARGED_FIELDS]
            # Filter empties then form multisets (as sorted lists) for deterministic diff.
            old_filtered = sorted([m for m in old_charged if m])
            new_filtered = sorted([m for m in new_charged if m])
            if old_filtered and new_filtered and old_filtered != new_filtered:
                # Identify removed and added moves (multiset difference simplified to set difference for readability)
                removed = sorted(set(old_filtered) - set(new_filtered))
                added = sorted(set(new_filtered) - set(old_filtered))
                if removed or added:
                    parts = []
                    if removed:
                        parts.append("-" + "/".join(removed))
                    if added:
                        parts.append("+" + "/".join(added))
                    diffs.append("Charged: " + " ".join(parts))
            if diffs:
                change_count += 1
                lines.append(
                    f"{change_count:2d}. {rec_new.pokemon} (score {rec_old.score:.1f} -> {rec_new.score:.1f})\n    "
                    + " | ".join(diffs)
                )

        if change_count == 0:
            lines.append("(No move set changes detected in the top selection)")
        else:
            lines.append("")
            lines.append(f"Total with move changes: {change_count}")

        new_only = [r for r in top_new if not old.get(r.name_key)]
        if new_only:
            lines.append("")
            lines.append(
                "New in top {n} (no previous move set to compare): ".format(
                    n=self.top_n
                )
                + ", ".join(sorted(r.pokemon for r in new_only))
            )

        return "\n".join(lines)
