"""Regression tests for original CSV-rank analysis scopes."""

import unittest
from pathlib import Path
from unittest.mock import patch

from pogo_gbl_analyzer.loader import RankingsLoader
from pogo_gbl_analyzer.main import main
from pogo_gbl_analyzer.models import RankingDataset, RankingRecord
from pogo_gbl_analyzer.processors import (
    MoveSetChangesProcessor,
    RankShiftProcessor,
    TypeTrendsProcessor,
    WinnersLosersProcessor,
)


def record(
    name: str,
    rank: int,
    score: float = 50,
    fast: str = "Old Fast",
    charged: tuple[str, str] = ("A", "B"),
    types: tuple[str, str] = ("water", ""),
) -> RankingRecord:
    """Create a record with deliberately independent rank and score."""
    return RankingRecord(
        name,
        score,
        rank,
        {
            "Fast Move": fast,
            "Charged Move 1": charged[0],
            "Charged Move 2": charged[1],
            "Type 1": types[0],
            "Type 2": types[1],
        },
    )


def dataset(*records: RankingRecord) -> RankingDataset:
    """Preserve supplied insertion order rather than sorting the fixture."""
    return RankingDataset("great", {rec.name_key: rec for rec in records})


class DirectionalScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old = dataset(
            record("OutsideGain", 500, 1),
            record("OutsideLoss", 101, 100),
            record("Melmetal", 79, 40),
            record("BoundaryGain", 200, 45),
            record("BoundaryLoss", 100, 60),
            record("WithinLoss", 8, 60),
            record("OldOnly", 1),
            record("Unchanged", 4),
        )
        self.new = dataset(
            record("OutsideGain", 101, 100),
            record("OutsideLoss", 500, 1),
            record("Melmetal", 7, 55),
            record("BoundaryGain", 100, 50),
            record("BoundaryLoss", 200, 40),
            record("WithinLoss", 9, 55),
            record("NewOnly", 1),
            record("Unchanged", 4),
        )

    def test_directional_boundaries_and_within_top_movements(self) -> None:
        for processor in (
            WinnersLosersProcessor(100, None),
            RankShiftProcessor(100, None),
        ):
            with self.subTest(processor=type(processor).__name__):
                report = processor.process(self.old, self.new)
                for name in ("Melmetal", "BoundaryGain", "BoundaryLoss", "WithinLoss"):
                    self.assertIn(name, report)
                for name in (
                    "OutsideGain",
                    "OutsideLoss",
                    "OldOnly",
                    "NewOnly",
                    "Unchanged",
                ):
                    self.assertNotIn(name, report)

    def test_filter_before_sorting_and_output_truncation(self) -> None:
        for processor, best_gain in (
            (WinnersLosersProcessor(100, 1), "Melmetal"),
            (RankShiftProcessor(100, 1), "BoundaryGain"),
        ):
            with self.subTest(processor=type(processor).__name__):
                report = processor.process(self.old, self.new)
                self.assertIn(best_gain, report)
                self.assertIn("BoundaryLoss", report)
                self.assertNotIn("OutsideGain", report)
                self.assertNotIn("OutsideLoss", report)
                self.assertNotIn("WithinLoss", report)
                self.assertEqual(report.count("(truncated)"), 2)

    def test_omitted_scope_is_unrestricted(self) -> None:
        for processor in (WinnersLosersProcessor(), RankShiftProcessor()):
            with self.subTest(processor=type(processor).__name__):
                report = processor.process(self.old, self.new)
                self.assertIn("OutsideGain", report)
                self.assertIn("OutsideLoss", report)

    def test_minimum_delta_is_inclusive(self) -> None:
        old = dataset(record("Exact", 10, 40), record("Small", 20, 40))
        new = dataset(record("Exact", 5, 45), record("Small", 19, 41))
        for processor in (
            WinnersLosersProcessor(20, None, 5),
            RankShiftProcessor(20, None, 5),
        ):
            with self.subTest(processor=type(processor).__name__):
                report = processor.process(old, new)
                self.assertIn("Exact", report)
                self.assertNotIn("Small", report)

    def test_score_direction_is_independent_of_rank_direction(self) -> None:
        old = dataset(record("ScoreGain", 1, 40), record("ScoreLoss", 100, 60))
        new = dataset(record("ScoreGain", 101, 60), record("ScoreLoss", 1, 40))
        report = WinnersLosersProcessor(100).process(old, new)
        self.assertNotIn("ScoreGain", report)
        self.assertIn("ScoreLoss", report)

    def test_current_csv_melmetal_remains_eligible_within_top_100(self) -> None:
        root = Path(__file__).resolve().parents[1]
        loader = RankingsLoader()
        old = loader.load_csv(
            root / "data/cp1500_all_overall_rankings_old.csv", "great"
        )
        new = loader.load_csv(
            root / "data/cp1500_all_overall_rankings_new.csv", "great"
        )
        self.assertEqual(old.records["Melmetal"].rank, 79)
        self.assertEqual(new.records["Melmetal"].rank, 7)
        self.assertIn(
            "Melmetal (old rank 79 -> new rank 7)",
            RankShiftProcessor(100, None).process(old, new),
        )
        self.assertIn(
            "Melmetal (old 88.0 -> new 91.2)",
            WinnersLosersProcessor(100, None).process(old, new),
        )


class MoveScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old = dataset(
            record("FormerTop", 2, 40),
            record("BothTop", 1, 40),
            record("Entrant", 9, 40),
            record("Outside", 4, 100),
            record("OldOnly", 3),
        )
        self.new = dataset(
            record("Outside", 4, 100, fast="New Fast"),
            record("FormerTop", 9, 40, fast="New Fast"),
            record("BothTop", 2, 40, fast="New Fast"),
            record("Entrant", 1, 40, fast="New Fast"),
            record("NewOnly", 3),
        )

    def test_union_by_rank_once_in_new_rank_order(self) -> None:
        report = MoveSetChangesProcessor(3).process(self.old, self.new)
        for number, name in enumerate(("Entrant", "BothTop", "FormerTop"), 1):
            self.assertIn(f"{number:2d}. {name}", report)
            self.assertEqual(report.count(name), 1)
        self.assertNotIn("Outside", report)
        self.assertIn("NewOnly", report)
        self.assertIn("Total with move changes: 3", report)

    def test_output_limit_after_union_comparison(self) -> None:
        report = MoveSetChangesProcessor(3, 2).process(self.old, self.new)
        self.assertIn("Entrant", report)
        self.assertIn("BothTop", report)
        self.assertNotIn("FormerTop", report)
        self.assertIn("Truncated to 2 changes out of 3", report)

    def test_charged_order_ignored_but_replacements_reported(self) -> None:
        old = dataset(record("Swapped", 1), record("Replaced", 2))
        new = dataset(
            record("Swapped", 1, charged=("B", "A")),
            record("Replaced", 2, charged=("B", "C")),
        )
        report = MoveSetChangesProcessor(2).process(old, new)
        self.assertNotIn("Swapped", report)
        self.assertIn("Charged: -A +C", report)

    def test_cli_omitted_scope_retains_50_fallback(self) -> None:
        old = dataset(record("Boundary", 50), record("Outside", 51))
        new = dataset(
            record("Boundary", 60, fast="New Fast"),
            record("Outside", 51, fast="New Fast"),
        )
        with (
            patch(
                "sys.argv",
                ["analyzer", "old.csv", "new.csv", "great", "--processor", "movesets"],
            ),
            patch.object(RankingsLoader, "load_csv", side_effect=[old, new]),
            patch.object(Path, "mkdir"),
            patch.object(Path, "write_text") as write_text,
            patch("builtins.print"),
        ):
            main()
        report = write_text.call_args.args[0]
        self.assertIn("Boundary", report)
        self.assertNotIn("Outside", report)


class TypeScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old = dataset(
            record("Outside", 3, 100, types=("ghost", "")),
            record("Faller", 2, 40, types=("water", "flying")),
            record("OldOnly", 1, 30, types=("fire", "fire")),
        )
        self.new = dataset(
            record("Outside", 3, 200, types=("ghost", "")),
            record("Faller", 4, 35, types=("water", "flying")),
            record("NewOnly", 2, 20, types=("grass", "poison")),
            record("AnotherNew", 1, 10, types=("grass", "grass")),
        )

    def test_independent_rank_scopes_and_full_distinct_type_credit(self) -> None:
        report = TypeTrendsProcessor(analyze_top_n=2).process(self.old, self.new)
        expected = {
            "water": "score 40.00->0.00; count 1->0",
            "flying": "score 40.00->0.00; count 1->0",
            "fire": "score 30.00->0.00; count 1->0",
            "grass": "score 0.00->30.00; count 0->2",
            "poison": "score 0.00->20.00; count 0->1",
        }
        for name, totals in expected.items():
            line = next((line for line in report.splitlines() if name in line), "")
            self.assertIn(totals, line)
        self.assertNotIn("ghost", report)

    def test_omitted_scope_includes_all_records(self) -> None:
        report = TypeTrendsProcessor().process(self.old, self.new)
        self.assertIn("ghost", report)
        self.assertIn("score 100.00->200.00; count 1->1", report)
        self.assertIn("score 40.00->35.00; count 1->1", report)

    def test_output_truncation_and_threshold_after_aggregation(self) -> None:
        report = TypeTrendsProcessor(1, 30, 2).process(self.old, self.new)
        self.assertIn("grass", report)
        self.assertIn("flying", report)
        for name in ("water", "fire", "poison", "ghost"):
            self.assertNotIn(name, report)


class EmptyScopeTests(unittest.TestCase):
    def test_empty_and_nonoverlapping_snapshots_are_safe(self) -> None:
        for processor in (
            WinnersLosersProcessor(2),
            RankShiftProcessor(2),
            MoveSetChangesProcessor(2),
            TypeTrendsProcessor(analyze_top_n=2),
        ):
            for old, new in (
                (dataset(), dataset()),
                (dataset(record("OldOnly", 1)), dataset()),
                (dataset(), dataset(record("NewOnly", 1))),
            ):
                with self.subTest(processor=type(processor).__name__, old=old, new=new):
                    self.assertIn("League: great", processor.process(old, new))


if __name__ == "__main__":
    unittest.main()
