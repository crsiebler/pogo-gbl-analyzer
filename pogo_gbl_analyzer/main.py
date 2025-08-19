from __future__ import annotations
import argparse
from pathlib import Path
from .processing import RankingsLoader, WinnersLosersProcessor
from .loader import RankingsLoader
from .processors import WinnersLosersProcessor, MoveSetChangesProcessor

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
    p.add_argument(
        "--top",
        type=int,
        default=25,
        help="How many winners/losers to show (default 25)",
    )
    p.add_argument(
        "--min-delta",
        type=float,
        default=0.1,
        help="Minimum absolute score delta to include (default 0.1)",
    )
    p.add_argument(
        "--old-top-n",
        dest="old_top_n",
        type=int,
        default=None,
        help="Restrict comparison to top N from old dataset (meta relevance)",
    )
    p.add_argument(
        "--include-emerging",
        action="store_true",
        help="When using --meta-top-n also list emerging winners outside old meta that now reach meta score threshold",
    )
    p.add_argument(
        "--processor",
        choices=["winners", "movesets"],
        default="winners",
        help="Which analysis to run: winners (default) or movesets",
    )
    p.add_argument(
        "--movesets-top-n",
        type=int,
        default=50,
        help="Top N (by new score) to inspect for move set changes when --processor movesets (default 50)",
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

    if args.processor == "winners":
        processor = WinnersLosersProcessor(
            top_n=args.top,
            min_abs_delta=args.min_delta,
            old_top_n_filter=args.old_top_n,
            include_outside_meta_winners=args.include_emerging,
        )
    else:
        processor = MoveSetChangesProcessor(top_n=args.movesets_top_n)
    report = processor.process(old_ds, new_ds)
    print(report)


if __name__ == "__main__":
    main()
