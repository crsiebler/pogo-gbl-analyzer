from __future__ import annotations
from typing import Dict, List, Tuple
from collections import defaultdict
from ..models import RankingDataset


class TypeTrendsProcessor:
    """Analyze rising and falling Pokémon types based on aggregate score deltas.

    For each type (including dual-types counted separately), computes:
      * old_total_score, new_total_score
      * delta (new - old)
      * count_old / count_new (number of entries containing the type)

    Ranks by absolute delta (positive = rising, negative = falling) and outputs
    the top N in each direction.
    """

    TYPE1_FIELD = "Type 1"
    TYPE2_FIELD = "Type 2"

    def __init__(
        self,
        top_n: int = 10,
        min_abs_delta: float = 0.5,
        old_top_n: int | None = None,
        new_top_n: int | None = None,
    ):
        self.top_n = top_n
        self.min_abs_delta = min_abs_delta
        self.old_top_n = old_top_n
        self.new_top_n = new_top_n

    def process(self, old: RankingDataset, new: RankingDataset) -> str:
        # Accumulate scores and counts.
        old_scores: Dict[str, float] = defaultdict(float)
        new_scores: Dict[str, float] = defaultdict(float)
        old_counts: Dict[str, int] = defaultdict(int)
        new_counts: Dict[str, int] = defaultdict(int)

        def add(
            rec_raw: Dict[str, str],
            score: float,
            scores: Dict[str, float],
            counts: Dict[str, int],
        ):
            t1 = rec_raw.get(self.TYPE1_FIELD, "").strip().lower()
            t2 = rec_raw.get(self.TYPE2_FIELD, "").strip().lower()
            seen: List[str] = []
            if t1:
                seen.append(t1)
            if t2 and t2 not in ("none", t1):
                seen.append(t2)
            for t in seen:
                scores[t] += score
                counts[t] += 1

        old_iter = old.records.values()
        new_iter = new.records.values()
        if self.old_top_n is not None:
            old_iter = sorted(old_iter, key=lambda r: r.score, reverse=True)[
                : self.old_top_n
            ]
        if self.new_top_n is not None:
            new_iter = sorted(new_iter, key=lambda r: r.score, reverse=True)[
                : self.new_top_n
            ]

        for rec in old_iter:
            add(rec.raw, rec.score, old_scores, old_counts)
        for rec in new_iter:
            add(rec.raw, rec.score, new_scores, new_counts)

        # Union of all types encountered.
        types = sorted(set(old_scores) | set(new_scores))
        deltas: List[Tuple[str, float, float, float, int, int]] = []
        for t in types:
            o = old_scores.get(t, 0.0)
            n = new_scores.get(t, 0.0)
            delta = n - o
            if abs(delta) >= self.min_abs_delta:
                deltas.append(
                    (t, o, n, delta, old_counts.get(t, 0), new_counts.get(t, 0))
                )

        # Sort rising by descending delta, falling by ascending delta.
        rising = [d for d in deltas if d[3] > 0]
        falling = [d for d in deltas if d[3] < 0]
        rising.sort(key=lambda x: x[3], reverse=True)
        falling.sort(key=lambda x: x[3])

        scope_parts: List[str] = []
        if self.old_top_n is not None:
            scope_parts.append(f"old top {self.old_top_n}")
        if self.new_top_n is not None:
            scope_parts.append(f"new top {self.new_top_n}")
        scope_suffix = " (" + ", ".join(scope_parts) + ")" if scope_parts else ""
        lines: List[str] = [
            f"League: {new.league}",
            f"Type Trends (aggregate score deltas){scope_suffix}",
        ]
        lines.append("")
        rising_slice = rising[: self.top_n]
        lines.append(f"Rising Types ({len(rising_slice)} Total)")
        for t, o, n, delta, co, cn in rising_slice:
            lines.append(
                f"+{delta:6.2f} {t:<10} (score {o:.2f}->{n:.2f}; count {co}->{cn})"
            )
        lines.append("")
        falling_slice = falling[: self.top_n]
        lines.append(f"Falling Types ({len(falling_slice)} Total)")
        for t, o, n, delta, co, cn in falling_slice:
            lines.append(
                f"{delta:7.2f} {t:<10} (score {o:.2f}->{n:.2f}; count {co}->{cn})"
            )

        return "\n".join(lines)
