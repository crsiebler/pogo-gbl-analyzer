from __future__ import annotations

from typing import List, Optional

from ..models import RankingDataset, RankingRecord


class MoveSetChangesProcessor:
    """Report move set changes for high-ranking Pokémon.

    Parameters:
      analyze_top_n: inspect the union of OLD and NEW rank <= N (CSV positions).
        Compare shared records once in NEW rank order; default 50.
      output_top_n: optional cap on how many change entries to print.
    """

    FAST_FIELD = "Fast Move"
    CHARGED_FIELDS = ["Charged Move 1", "Charged Move 2"]

    def __init__(
        self, analyze_top_n: int = 50, output_top_n: int | None = None
    ) -> None:
        self.analyze_top_n = analyze_top_n
        self.output_top_n = output_top_n

    def process(self, old: RankingDataset, new: RankingDataset) -> str:
        scope_keys = {
            key
            for snapshot in (old, new)
            for key, rec in snapshot.records.items()
            if rec.rank <= self.analyze_top_n
        }
        selected_new = sorted(
            (rec for key, rec in new.records.items() if key in scope_keys),
            key=lambda rec: rec.rank,
        )
        lines: List[str] = [
            f"League: {new.league}",
            f"Move Set Changes Among OLD or NEW Top {self.analyze_top_n} by CSV rank (union: {len(scope_keys)}; ordered by new rank)",
        ]

        change_entries: List[str] = []

        for rec_new in selected_new:
            rec_old: Optional[RankingRecord] = old.get(rec_new.name_key)
            if not rec_old:
                continue
            diffs: List[str] = []
            fast_old = rec_old.raw.get(self.FAST_FIELD, "").strip()
            fast_new = rec_new.raw.get(self.FAST_FIELD, "").strip()
            if fast_old and fast_new and fast_old != fast_new:
                diffs.append(f"Fast: {fast_old} -> {fast_new}")
            old_charged = [rec_old.raw.get(f, "").strip() for f in self.CHARGED_FIELDS]
            new_charged = [rec_new.raw.get(f, "").strip() for f in self.CHARGED_FIELDS]
            old_filtered = sorted([m for m in old_charged if m])
            new_filtered = sorted([m for m in new_charged if m])
            if old_filtered and new_filtered and old_filtered != new_filtered:
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
                change_entries.append(
                    f"{len(change_entries) + 1:2d}. {rec_new.pokemon} (score {rec_old.score:.1f} -> {rec_new.score:.1f})\n    "
                    + " | ".join(diffs)
                )

        total_changes = len(change_entries)
        if self.output_top_n is not None and total_changes > self.output_top_n:
            displayed = change_entries[: self.output_top_n]
            displayed.append(
                f"(Truncated to {self.output_top_n} changes out of {total_changes})"
            )
            lines.extend(displayed)
        else:
            lines.extend(change_entries)

        if total_changes == 0:
            lines.append("(No move set changes detected in the top selection)")
        else:
            lines.append("")
            lines.append(f"Total with move changes: {total_changes}")

        new_only = [r for r in selected_new if not old.get(r.name_key)]
        if new_only:
            lines.append("")
            lines.append(
                "New in top {n} (no previous move set to compare): ".format(
                    n=self.analyze_top_n
                )
                + ", ".join(sorted(r.pokemon for r in new_only))
            )

        return "\n".join(lines)
