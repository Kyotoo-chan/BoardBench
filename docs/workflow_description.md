# BoardBench workflow

## Interactive use

```text
/bbedge game=<slug>
/bbimpl game=<slug>
/bbeval game=<slug>
```

`/bb` reports the next phase. Pi skills orchestrate; executable behavior lives in Python and JSON under `checks/` and `generation/`.

## Phases

1. **Source analysis:** archive the rulebook, cite facts, and resolve material ambiguities with the user.
2. **Isolated implementation:** give one Codex agent only its assigned source, interface contract, and evaluator-neutral self-check. Require `implementation.py`, `rule_coverage.md`, and `assumptions.json`.
3. **Mechanical evaluation:** run checks 01–06 and deterministic cited scenarios.
4. **Blind review:** run three neutral judges and three separate personas without exposing checks or other implementations.
5. **Reporting:** write JSON/Markdown under `results/scores/<game>/<run>/` and optional PNGs under `results/plots/<game>/<run>/`.
6. **Iteration:** when a source, test, or evaluator defect is found, correct the current workflow and run again. Git and recorded hashes identify what earlier runs used.

## Current native defaults

- implementation: `gpt-5.6-sol:low`;
- judges: `gpt-5.6-sol:medium`.

Evidence groups remain separate. Every failure is attributed rather than automatically blamed on the rulebook or implementation.
