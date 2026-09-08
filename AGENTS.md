# Repository Guidance

## Running and Verification

- Use Python 3.11+ for the CLI (`main.py` imports `datetime.UTC`), despite the README's 3.10+ recommendation. Runtime dependencies are standard-library only; there is no package manifest or install step.
- Run from the repository root: `python3 -m pogo_gbl_analyzer.main OLD_CSV NEW_CSV great --processor winners`. Processor choices are `winners`, `movesets`, `types`, and `ranks`; `all` is Makefile-only.
- `make` runs all three leagues and all four processors with `ANALYZE_TOP_N=100`, `OUTPUT_TOP_N=25`, and `MIN_DELTA=0.1`. Focus a run with `make great PROCESSOR=winners OUTPUT_TOP_N=5`; override the interpreter with `PYTHON=...`.
- `make great PROCESSOR=winners ANALYZE_TOP_N=` omits the scope flag. Direct CLI defaults differ from Make: processor `winners`, no scope limit except the movesets fallback of 50.
- Analysis runs write `output/{league}_{processor}_{UTC timestamp}.txt` relative to the working directory; stdout only prints the path. Reports are not gitignored, so smoke runs create untracked files. Call a processor's `process(old, new)` directly for an in-memory report.
- No test suite, CI, lint, formatter, or typecheck configuration is present. `python3 -m pogo_gbl_analyzer.main --help` checks CLI imports without writing reports; `make -n great PROCESSOR=winners` checks command expansion without running analysis. Neither is a behavioral test.
- The Makefile's all-processors shell loop does not fail fast; a successful final processor can mask an earlier failure. Verify a changed processor with an explicit `PROCESSOR=...` run.

## Implementation Boundaries

- The active path is `main.py` -> `loader.py` / `models.py` -> `processors/`. `processing.py` is an older duplicate with incompatible models/options, not used by the CLI or package exports; do not mistake it for the active implementation.
- Processors implement `process(old: RankingDataset, new: RankingDataset) -> str`; file output belongs to `main.py`. Adding a CLI processor requires exporting it in `processors/__init__.py`, wiring its choice and construction in `main.py`, and updating the Makefile loop if it should run with `all`.

## Data and Analysis Semantics

- CSVs require exact `Pokemon` and `Score` headers; extra columns remain in `RankingRecord.raw`. Names are stripped but otherwise matched exactly, so shadow/forms stay distinct. Rank is assigned during loading from encounter order, not calculated by sorting scores.
- `--analyze-top-n` scopes records by original CSV rank, not by score and without a score floor. `winners` and `ranks` use NEW top N for gains/climbers and OLD top N for losses/droppers; movements that stay within the top N remain eligible. When omitted, both processors compare all matching records.
- `movesets` inspects the union of OLD and NEW top N by CSV rank, compares each shared Pokemon once in NEW-rank order, and ignores charged-move ordering. It reads `Fast Move`, `Charged Move 1`, and `Charged Move 2` from raw fields. If omitted from the CLI, it defaults internally to 50.
- `types` scopes BOTH snapshots independently by CSV rank, reads `Type 1` / `Type 2`, and credits the full score to each distinct type of a dual-typed entry. Entries without a counterpart still contribute to their own snapshot total.
- For `ranks`, the CLI converts a nonzero `--min-delta` to `int`; use `--min-delta 1` explicitly for a one-position threshold rather than relying on the shared default of `0.1`.
