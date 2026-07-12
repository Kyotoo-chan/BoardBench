# Current state

BoardBench is a manual-first, agentic rulebook-to-environment workflow. The repository is preparing a controlled bachelor-thesis study, not claiming to be a finished universal benchmark.

## Primary interface

Project-local pi skills:

- `/skill:bb`
- `/skill:bbedge`
- `/skill:bbimpl`
- `/skill:bbeval`

The parent defaults to `openai-codex/gpt-5.6-sol:low`. Commands accept `subagents`, `submodel`, and `subthinking`; absent explicit settings, children inherit or use only demonstrably weaker capability.

## Workflow state per game

```text
inputs/games/<slug>/game_rules.pdf|txt
inputs/games/<slug>/rulefacts.md
checks/scenarios/<slug>.json
outputs/<slug>_<backend>_ag.md
outputs/<slug>_<backend>_ag.py
outputs/<slug>_<backend>_ag_checks.txt
outputs/<slug>_<backend>_ag_judge_<label>.md
```

The active drop location remains `inputs/game_rules.pdf` or `.txt`.

## Evaluation

- 01–04: technical gate
- 05: sampled runtime robustness
- 06: action-language interface
- `run_scenarios.py`: rulebook-cited black-box behaviour
- 90: saved judge signal
- 99: optional OpenSpiel agreement

OpenSpiel is secondary. New games must remain evaluable without it. Values from unlike groups are not a single correctness measure.

## Historical infrastructure

One-shot notebooks, pair comparison, and manual Exploding-Kittens testing were removed from the working tree; Git history preserves them. `evaluation.ipynb` is now agentic-only. Old plots remain pilot artifacts and are not the default workflow.

See `docs/workflow_description.md` for usage and `docs/projektgespraech_offene_fragen_und_weiterarbeit.md` for current research decisions.
