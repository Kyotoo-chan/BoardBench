# BoardBench workflow

The workflow detects problems in an executable translation of the original rulebook, turns supported source gaps into visible clarifications, and generates again to test whether those problems are reduced. Remaining questions are evidence, not unfinished game-development work.

## Interactive use

```text
/bbedge game=<slug>
/bbimpl game=<slug>
/bbeval game=<slug>
```

`/bb` reports the next phase. Pi skills orchestrate; executable behavior lives in Python and JSON under `checks/` and `generation/`.

## Phases

1. **Source analysis:** archive and hash every document in the assigned source condition (including an explicitly required, edition-matched publisher companion when applicable), cite facts, and record material ambiguities plus approved evaluator interpretations without adding them to the canonical implementer input.
2. **Isolated implementation:** give one Codex agent only its assigned source, interface contract, and evaluator-neutral self-check. Require `implementation.py`, `rule_coverage.md`, and `assumptions.json`.
3. **Mechanical evaluation:** run checks 01–06 and deterministic cited scenarios.
4. **Blind review:** run three neutral judges and three separate personas without exposing checks or other implementations.
5. **Reporting:** write JSON/Markdown under `results/scores/<game>/<run>/` and optional PNGs under `results/plots/<game>/<run>/`.
6. **Iteration:** when a source, test, or evaluator defect is found, correct the current workflow and run again. Git and recorded hashes identify what earlier runs used.

## Current native defaults

- implementation: `gpt-5.6-sol:low`;
- judges: `gpt-5.6-sol:medium`;
- response verbosity: `low`.

Evidence groups remain separate. Every failure is attributed rather than automatically blamed on the rulebook or implementation.
