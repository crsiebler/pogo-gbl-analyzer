from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from .loader import RankingsLoader
from .processors import (
    BaseRankingProcessor,
    MoveSetChangesProcessor,
    RankShiftProcessor,
    TypeTrendsProcessor,
    WinnersLosersProcessor,
)

LEAGUE_ALIASES = {
    "great": "great",
    "g": "great",
    "1500": "great",
    "ultra": "ultra",
    "u": "ultra",
    "2500": "ultra",
    "master": "master",
    "m": "master",
    "10000": "master",
}


def parse_args():
    p = argparse.ArgumentParser(description="Compare PvPoke ranking CSV exports.")
    p.add_argument("old", type=Path, help="Old rankings CSV file")
    p.add_argument("new", type=Path, help="New rankings CSV file")
    p.add_argument(
        "league",
        help="League identifier: great|ultra|master (aliases: 1500,2500,10000)",
    )
    # Unified flags
    p.add_argument(
        "--analyze-top-n",
        type=int,
        default=None,
        help=(
            "Scope by original CSV rank <= N: winners/ranks use NEW for gains "
            "and OLD for losses; movesets uses the OLD/NEW union; types scopes "
            "each snapshot independently. Includes movements within top N, with "
            "no score floor. Omitted: unrestricted except movesets defaults to 50."
        ),
    )
    p.add_argument(
        "--output-top-n",
        type=int,
        default=25,
        help="Rows per list after scope filtering and sorting (winners/losers, climbers/droppers, rising/falling types, or move changes).",
    )
    p.add_argument(
        "--min-delta",
        type=float,
        default=0.1,
        help=(
            "Minimum absolute score delta (winners/types). Default 0.1. "
            "For ranks, nonzero values are converted to integer positions; "
            "use 1 explicitly for a one-position threshold."
        ),
    )
    p.add_argument(
        "--processor",
        choices=["winners", "movesets", "types", "ranks"],
        default="winners",
        help=(
            "Select analysis: "
            "winners (score deltas), "
            "movesets (move changes in OLD/NEW top N union by CSV rank), "
            "types (aggregate rising/falling types), "
            "ranks (rank position shifts)."
        ),
    )
    return p.parse_args()


def normalize_league(value: str) -> str:
    key = value.lower()
    if key not in LEAGUE_ALIASES:
        raise SystemExit(f"Unknown league '{value}'. Use one of: great, ultra, master")
    return LEAGUE_ALIASES[key]


def main():
    args = parse_args()
    league = normalize_league(args.league)

    loader = RankingsLoader()
    old_ds = loader.load_csv(args.old, league)
    new_ds = loader.load_csv(args.new, league)

    processor: BaseRankingProcessor
    if args.processor == "winners":
        processor = WinnersLosersProcessor(
            analyze_top_n=args.analyze_top_n,
            output_top_n=args.output_top_n,
            min_abs_delta=args.min_delta,
        )
    elif args.processor == "movesets":
        processor = MoveSetChangesProcessor(
            analyze_top_n=args.analyze_top_n if args.analyze_top_n else 50,
            output_top_n=args.output_top_n,
        )
    elif args.processor == "types":
        processor = TypeTrendsProcessor(
            output_top_n=args.output_top_n,
            min_abs_delta=args.min_delta,
            analyze_top_n=args.analyze_top_n,
        )
    elif args.processor == "ranks":
        processor = RankShiftProcessor(
            analyze_top_n=args.analyze_top_n,
            output_top_n=args.output_top_n,
            min_rank_delta=int(args.min_delta) if args.min_delta else 1,
        )
    report = processor.process(old_ds, new_ds)
    # Write to output directory
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    filename = f"{league}_{args.processor}_{timestamp}.txt"
    out_path = out_dir / filename
    out_path.write_text(report, encoding="utf-8")
    print(f"[written] {out_path}")


if __name__ == "__main__":
    main()
