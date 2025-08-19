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
│       └── type_trends.py      # TypeTrendsProcessor (rising/falling types)
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
| `MoveSetChangesProcessor` | Lists move set changes (Fast/Charged) for high‑ranking current Pokémon. |

The modular layout (`models.py`, `loader.py`, and the `processors/` package) isolates responsibilities so adding new analyses is straightforward.

## CLI
Run via the module form:
```bash
python -m pogo_gbl_analyzer.main OLD_CSV NEW_CSV great
```

The `Makefile` offers shortcuts for the bundled sample data (variable names shown may still reference earlier flag names; see the unified flags below for current usage).

### Unified CLI Arguments
The interface was simplified to a small, consistent set of flags. Deprecated flags such as `--top`, `--old-top-n`, `--include-emerging`, `--movesets-top-n`, `--types-old-top-n`, and `--types-new-top-n` were removed.

| Argument | Description |
|----------|-------------|
| `old` | Path to previous ("old") CSV export. |
| `new` | Path to current ("new") CSV export. |
| `league` | One of `great`, `ultra`, `master` (aliases: `1500`, `2500`, `10000`). |
| `--processor {winners,movesets,types}` | Select analysis: Pokémon deltas, move set changes, or type trends. Default `winners`. |
| `--analyze-top-n N` | Limit analysis scope to the top N Pokémon of each snapshot (winners uses NEW only; movesets uses NEW; types applies to BOTH old & new). If omitted: winners uses full dataset; movesets defaults to 50 internally; types uses full snapshots. |
| `--output-top-n N` | Number of rows (winners list, losers list, type rows, or move changes) to display. Default 25. |
| `--min-delta D` | Minimum absolute score change to include (applies to winners & types). Default 0.1. |

### Notes
* The previous "emerging" meta concept was removed for simplicity.
* Move set comparison ignores charged move ordering (treats them as an unordered set).
* Dual‑typed Pokémon contribute their score to both types in type trend aggregation.

## Example Runs
Basic Great League winners/losers (show 20 rows each):
```bash
python -m pogo_gbl_analyzer.main \
  data/cp1500_all_overall_rankings_old.csv \
  data/cp1500_all_overall_rankings_new.csv \
  great --output-top-n 20
```

Move set changes among top 60 Ultra League Pokémon (show up to 30 changes):
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
Computes individual Pokémon score deltas, showing biggest winners and losers. Use `--analyze-top-n` to restrict to the top portion of the NEW snapshot (otherwise all Pokémon are considered). Results are truncated with `--output-top-n`.

### MoveSetChangesProcessor
Lists Fast / Charged move set changes among high‑ranking Pokémon in the NEW snapshot. Use `--analyze-top-n` to define how many of the top new Pokémon to inspect (default internal fallback of 50 if omitted). Charged move ordering is ignored; additions and removals are reported. Control output length with `--output-top-n`.

### TypeTrendsProcessor
Aggregates total score per type and reports rising and falling types based on aggregate score delta and counts. Use `--analyze-top-n` to restrict both snapshots to their respective top N before aggregation. Use `--output-top-n` to limit displayed rising / falling lists and `--min-delta` to suppress small movements.

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
* Pure standard library (Python 3.10+ recommended). No external dependencies.
* CSV columns required: `Pokemon`, `Score`. Additional columns are retained in `raw` for future processors.
* Normalization of names is currently 1:1; if alias resolution is needed add logic in `RankingRecord.name_key`.

## License
MIT (see `LICENSE`).

## Future Ideas
* Additional processors: volatility index, move set change summaries, coverage vs core meta.
* JSON export option for integration with dashboards.
* Unit tests for processor behaviors.
