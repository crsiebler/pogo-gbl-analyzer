# pogo-gbl-analyzer

Analyze Pokémon GO GO Battle League (GBL) ranking CSV exports (e.g. from PvPoke) to surface the biggest winners and losers between two snapshots of the meta.

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
│   ├── main.py                # CLI entry: python -m pogo_gbl_analyzer.main ...
│   └── processing.py          # Data models + processor interface + implementation
│   ├── models.py              # RankingRecord / RankingDataset
│   ├── loader.py              # RankingsLoader
│   └── processors/
│       ├── __init__.py
│       ├── base.py            # BaseRankingProcessor protocol
│       └── winners_losers.py  # WinnersLosersProcessor implementation
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
| `WinnersLosersProcessor` | Computes score deltas (biggest winners/losers, emerging picks). |

`processing.py` contains both the data abstractions and the first concrete processor. You can add more processors later (e.g. usage shift, typing distribution) by implementing the protocol.
Separated modules: `models.py`, `loader.py`, and `processors/` package isolate responsibilities for easier extension.

## Script & CLI
Two interchangeable entry points expose the comparison functionality:

1. Module form (always available):
   ```bash
   python -m pogo_gbl_analyzer.main OLD_CSV NEW_CSV great
   ```
2. Convenience script:
   ```bash
   ./scripts/compare_rankings.py OLD_CSV NEW_CSV ultra --top 40
   ```

A `Makefile` provides shortcuts assuming the default file naming:
```bash
make great              # Uses cp1500 old/new files
make ultra TOP=40       # Override number of winners/losers
make master OLD_TOP_N=50 EMERGING=1  # Focus on old top 50 + show emerging
```

## CLI Arguments
| Argument | Description |
|----------|-------------|
| `old` | Path to previous ("old") CSV export. |
| `new` | Path to current ("new") CSV export. |
| `league` | One of `great`, `ultra`, `master` (aliases: `1500`, `2500`, `10000`). |
| `--top N` | Number of winners and losers to list (default 25). |
| `--min-delta D` | Minimum absolute score change to report (default 0.1). |
| `--old-top-n N` | Restrict comparison universe to the old top N (meta focus). |
| `--include-emerging` | When filtering, also list entrants outside the old meta that now meet the previous threshold. |

### Emerging Winners Logic
When `--old-top-n` is supplied the minimum score among that subset defines the previous meta threshold. With `--include-emerging`, Pokémon outside the original subset are included if:
1. Their new score ≥ old threshold; and
2. They improved by at least `--min-delta` (or are brand new with score ≥ threshold).

## Example Runs
Great League basic run:
```bash
python -m pogo_gbl_analyzer.main \
  data/cp1500_all_overall_rankings_old.csv \
  data/cp1500_all_overall_rankings_new.csv \
  great --top 20
```

Ultra League with meta restriction & emerging:
```bash
python -m pogo_gbl_analyzer.main \
  data/cp2500_all_overall_rankings_old.csv \
  data/cp2500_all_overall_rankings_new.csv \
  ultra --old-top-n 50 --include-emerging --min-delta 0.2
```

Master League via script:
```bash
./scripts/compare_rankings.py \
  data/cp10000_all_overall_rankings_old.csv \
  data/cp10000_all_overall_rankings_new.csv \
  master --top 30
```

## Extending the Analyzer
1. Create a new processor class implementing `process(old: RankingDataset, new: RankingDataset) -> str`.
2. Optionally add argument(s) to `main.py` / `compare_rankings.py` to select it.
3. Register and dispatch similarly to how `WinnersLosersProcessor` is used.

Because the data layer is decoupled, additional analyses (e.g. percentile shifts, type coverage changes) can reuse the loader and datasets.

## Development Notes
* Pure standard library (Python 3.10+ recommended). No external dependencies.
* CSV columns required: `Pokemon`, `Score`. Additional columns are retained in `raw` for future processors.
* Normalization of names is currently 1:1; if alias resolution is needed add logic in `RankingRecord.name_key`.

## License
MIT (see `LICENSE`).

## Future Ideas
* Additional processors: volatility index, rising/falling types, move-set impact.
* JSON export option for integration with dashboards.
* Unit tests for processor behaviors.
