# BoardBench

BoardBench turns one board-game rulebook into a Python environment and evaluates rule fidelity with cited evidence.

## Workflow

Generated evidence is stored under `results/scores/<game>/<run>/`; `results/plots/<game>/<run>/` contains images only. Native Codex defaults are `gpt-5.6-sol:low` for implementation generation and `gpt-5.6-sol:medium` for judges.

1. Put one rulebook at `inputs/game_rules.pdf` or `.txt`.
2. `/bbedge game=<slug>` — extract cited facts, resolve ambiguities, approve scenarios.
3. `/bbimpl game=<slug>` — generate one implementation in an isolated workspace.
4. `/bbeval game=<slug>` — run grouped checks and independent rule review.

Use `/bb game=<slug>` for status.

Optional child settings:

```text
subagents=on|off|auto submodel=<provider/model> subthinking=<level>
```

Without explicit settings, children inherit or use only weaker capability than the parent.

## Evaluation

Results stay separate:

- technical checks 01–04
- runtime robustness 05
- interface 06
- cited rule scenarios
- independent LLM review
- optional OpenSpiel reference

Run Python through the `boardbench` Conda environment. See `AGENTS.md` and `docs/workflow_description.md` for details.
