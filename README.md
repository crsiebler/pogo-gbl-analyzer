# pogo-gbl-analyzer

Analyze Pokémon GO GO Battle League (GBL) ranking CSV exports (e.g. from PvPoke) to surface the biggest winners/losers, rising/falling types, and other meta shifts between two snapshots.

## Overview (From Initial Prompt)
The repository ships with 6 CSV files exported from PvPoke representing rankings for the three PvP leagues:

* Great League (CP 1500 cap) – files prefixed `cp1500_...`
* Ultra League (CP 2500 cap) – files prefixed `cp2500_...`
* Master League (no CP cap; `cp10000_` used as a stand‑in upper bound) – files prefixed `cp10000_...`

For each league there is an `*_old.csv` (previous snapshot) and an `*_new.csv` (current snapshot). Each row represents a distinct Pokémon form (e.g. `Lapras` vs `Lapras (Shadow)` are separate). The key numeric metric compared is `Score`.

## Project Structure
```
├── data/
│   ├── cp1500_all_overall_rankings_old.csv
│   ├── cp1500_all_overall_rankings_new.csv
│   ├── cp2500_all_overall_rankings_old.csv
│   ├── cp2500_all_overall_rankings_new.csv
│   ├── cp10000_all_overall_rankings_old.csv
│   └── cp10000_all_overall_rankings_new.csv
├── pogo_gbl_analyzer/
│   ├── __init__.py
│   ├── main.py                 # CLI entry: python -m pogo_gbl_analyzer.main ...
│   ├── models.py               # RankingRecord / RankingDataset
│   ├── loader.py               # RankingsLoader
│   └── processors/
│       ├── __init__.py
│       ├── base.py             # BaseRankingProcessor protocol
│       ├── winners_losers.py   # WinnersLosersProcessor implementation
│       ├── move_changes.py     # MoveSetChangesProcessor (move set diffs)
│       ├── type_trends.py      # TypeTrendsProcessor (rising/falling types)
│       └── rank_shift.py       # RankShiftProcessor (climbers/droppers)
├── tests/test_analysis_scope.py # unittest scope regressions
├── Makefile                   # make great|ultra|master helpers
└── README.md
```

## Core Library (`pogo_gbl_analyzer`)
| Component | Purpose |
|-----------|---------|
| `RankingRecord` | Represents one Pokémon row (score + raw fields). |
| `RankingDataset` | Collection of records for a specific league. |
| `RankingsLoader` | Validates & loads a ranking CSV into a dataset. |
| `BaseRankingProcessor` | Protocol (interface) describing a processor. |
| `WinnersLosersProcessor` | Computes score deltas (biggest winners / losers) between snapshots. |
| `MoveSetChangesProcessor` | Lists move set changes (Fast/Charged) for high-ranking Pokémon in either snapshot. |
| `RankShiftProcessor` | Computes rank improvements and falls between snapshots. |
| `TypeTrendsProcessor` | Compares independently aggregated type scores and counts. |

The modular layout (`models.py`, `loader.py`, and the `processors/` package) isolates responsibilities so adding new analyses is straightforward.

## CLI
Run via the module form:
```bash
python -m pogo_gbl_analyzer.main OLD_CSV NEW_CSV great
```

The `Makefile` offers shortcuts for the bundled sample data. Unlike the direct CLI, `make` defaults to all four processors in all three leagues, `ANALYZE_TOP_N=100`, `OUTPUT_TOP_N=25`, and `MIN_DELTA=0.1`. Use `make great PROCESSOR=winners` for one report, or `ANALYZE_TOP_N=` to omit the scope flag (movesets still falls back to 50).

### Unified CLI Arguments
The interface was simplified to a small, consistent set of flags. Deprecated flags such as `--top`, `--old-top-n`, `--include-emerging`, `--movesets-top-n`, `--types-old-top-n`, and `--types-new-top-n` were removed.

| Argument | Description |
|----------|-------------|
| `old` | Path to previous ("old") CSV export. |
| `new` | Path to current ("new") CSV export. |
| `league` | One of `great`, `ultra`, `master` (aliases: `1500`, `2500`, `10000`). |
| `--processor {winners,movesets,types,ranks}` | Select score deltas, move set changes, type trends, or rank shifts. Default `winners`. |
| `--analyze-top-n N` | Use original CSV rank <= N, not score sorting: winners/ranks scope gains to NEW and losses to OLD; movesets uses the OLD/NEW union; types scopes each snapshot independently. Omitted: winners/ranks/types unrestricted, movesets defaults to 50. |
| `--output-top-n N` | Rows per winners/losers, climbers/droppers, or rising/falling list, or total move changes, after scope filtering and sorting. Default 25. |
| `--min-delta D` | Minimum absolute score change for winners/types. Default 0.1. Ranks converts nonzero values to integer positions; use `--min-delta 1` explicitly for a one-position threshold. |

### Notes
* The previous "emerging" meta concept was removed for simplicity.
* Rank is the original `RankingRecord.rank` assigned from CSV encounter order. Scores and tied scores never redefine the top N. There is no 80-point (or other) score floor.
* Directional scopes include movements within the top N, not just entrants/exits: Melmetal moving from rank 79 to 7 is eligible with N=100.
* Move set comparison ignores charged move ordering (treats them as an unordered set).
* Score, rank, and move comparisons require both snapshots. Missing counterparts are skipped safely; new-only top entries are noted in moveset reports.
* Dual-typed Pokémon contribute their full score once to each distinct type. Type totals include entries missing a counterpart in their own snapshot.
* Reports are written to new timestamped `output/{league}_{processor}_{UTC timestamp}.txt` paths; stdout prints the path. Timestamps have second precision, so avoid repeating the same league/processor within one second to prevent overwriting a report.

## Example Runs
Basic Great League winners/losers (show 20 rows each):
```bash
python -m pogo_gbl_analyzer.main \
  data/cp1500_all_overall_rankings_old.csv \
  data/cp1500_all_overall_rankings_new.csv \
  great --output-top-n 20
```

Move set changes among the union of OLD and NEW top 60 Ultra League Pokémon by rank (show up to 30 changes):
```bash
python -m pogo_gbl_analyzer.main \
  data/cp2500_all_overall_rankings_old.csv \
  data/cp2500_all_overall_rankings_new.csv \
  ultra --processor movesets --analyze-top-n 60 --output-top-n 30
```

Type trends focusing on top 100 of both snapshots, displaying top 15 rising/falling types with a 1.0 min delta filter:
```bash
python -m pogo_gbl_analyzer.main \
  data/cp10000_all_overall_rankings_old.csv \
  data/cp10000_all_overall_rankings_new.csv \
  master --processor types --analyze-top-n 100 --output-top-n 15 --min-delta 1.0
```

## Processors

### WinnersLosersProcessor
Computes individual Pokémon score deltas. With `--analyze-top-n N`, positive score changes require NEW rank <= N and negative changes require OLD rank <= N. Both directions remain unrestricted if omitted. Eligible changes are sorted by score delta before `--output-top-n` truncation.

### RankShiftProcessor
Computes rank shifts as OLD rank minus NEW rank. With `--analyze-top-n N`, climbers require NEW rank <= N and droppers require OLD rank <= N. Movements within the top N remain eligible. Both directions are unrestricted if omitted. Scope filtering precedes sorting by rank shift and output truncation. Example: `make great PROCESSOR=ranks ANALYZE_TOP_N=100 MIN_DELTA=1`.

### MoveSetChangesProcessor
Lists Fast / Charged move set changes in the union of OLD rank <= N and NEW rank <= N. Shared entries are compared once, ordered by NEW rank, so former top entries remain eligible even after falling outside N. `--analyze-top-n` defaults internally to 50 if omitted. Charged move ordering is ignored; additions and removals are reported. `--output-top-n` truncates changes after comparison.

### TypeTrendsProcessor
Aggregates total score per type and reports rising and falling types based on aggregate score delta and counts. `--analyze-top-n` restricts each snapshot independently to its original rank <= N before aggregation, without requiring matching entries in the other snapshot. Omitted scope uses full snapshots. Each distinct type receives the full score with no score floor. Use `--output-top-n` to limit displayed rising / falling lists and `--min-delta` to suppress small aggregate movements.

### Additional Examples
Move set changes (top 40 Master League, show 25):
```bash
python -m pogo_gbl_analyzer.main \
  data/cp10000_all_overall_rankings_old.csv \
  data/cp10000_all_overall_rankings_new.csv \
  master --processor movesets --analyze-top-n 40 --output-top-n 25
```

Type trends (Great League, unrestricted full snapshots, show 10):
```bash
python -m pogo_gbl_analyzer.main \
  data/cp1500_all_overall_rankings_old.csv \
  data/cp1500_all_overall_rankings_new.csv \
  great --processor types --output-top-n 10
```

## Extending the Analyzer
1. Create a new processor class implementing `process(old: RankingDataset, new: RankingDataset) -> str`.
2. Export it from `processors/__init__.py`.
3. Add a CLI `--processor` choice (and any custom flags) in `main.py`.
4. (Optionally) update the Makefile to surface a variable mapping.

Because the data layer is decoupled, additional analyses (e.g. percentile shifts, usage volatility, coverage indices) can reuse the loader and datasets.

## Development Notes
* Pure standard library (Python 3.11+ required). No runtime dependencies or install step.
* CSV columns required: `Pokemon`, `Score`. Additional columns are retained in `raw` for future processors.
* Normalization of names is currently 1:1; if alias resolution is needed add logic in `RankingRecord.name_key`.
* Run regressions: `python3 -m unittest discover -s tests -v`. The Melmetal integration regression intentionally uses the current bundled Great League CSV snapshots; update its expectations when replacing those snapshots.
* Import/help check: `python3 -m pogo_gbl_analyzer.main --help`. Dry-run: `make -n great PROCESSOR=winners`. Neither replaces behavioral tests.
* Tooling is configured in `pyproject.toml`. Run `ruff check .` for lint/import checks, `ruff format --check .` for formatting validation, and `mypy` for typechecking the active package and tests. The unused legacy `processing.py` is excluded from mypy but remains covered by Ruff.
* To apply formatting and import sorting with installed tools, run `ruff check --fix .` followed by `ruff format .`. Development tools are separate from the standard-library runtime.
* For report generation, run each league/processor explicitly and check each exit status. The Makefile's all-processors loop does not fail fast and can mask earlier failures. Override `PYTHON` if your default interpreter is older than 3.11.

## License
MIT (see `LICENSE`).

## Future Ideas
* Additional processors: volatility index, move set change summaries, coverage vs core meta.
* JSON export option for integration with dashboards.
