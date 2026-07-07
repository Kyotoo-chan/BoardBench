---
name: boardbench-game-run
description: >-
  Per-backend BoardBench experiment git workflow: one generation commit (oneshot +
  agentic together), one test/judge commit, one plot pin commit. outputs/ clears
  automatically on prepare and before each backend's oneshot run. Use when saving
  run artifacts or spacing thesis commits.
---

# BoardBench per-backend git workflow

One backend per cycle, **both variants in the same commit**. No separate clear commit.

## Cycle (repeat per backend)

1. **Prepare** (first run for a game only): `python generation/game_run_workflow.py prepare <game>` — clears `outputs/` and activates rulebook. Commit `inputs/game_rules.pdf` (+ brief on first run).
2. **Generate both variants** (`oneshot` then `agentic`). Oneshot start auto-clears `outputs/`.
3. **Commit generation** — all four files: `{stem_os}.py/.md`, `{stem_ag}.py/.md`.
4. **Tests + judges** for both variants — cross judges **gpt + codex only**:
   `python generation/run_cross_judges.py --game <game> --impl-backend <backend> --judges gpt,codex`
   Refresh both check logs:
   `python -c "from generation.run_pilot_checks import refresh_run; refresh_run('<game>','<impl>','oneshot', rerun_base=False); refresh_run('<game>','<impl>','agentic', rerun_base=False)"`
5. **Commit tests** — both variants' `*_checks.txt`, `*_judge_gpt.md`, `*_judge_codex.md`.
6. **Pin + plot both variants** — `python generation/game_run_workflow.py plot --game <game> --backend <backend>`
   (auto-clears `outputs/` run artifacts after pin; scores stay in `plots/`)
7. **Commit plot** — `plots/<slug>_pinned.json`, `plots/<slug>_scores.png`, `plots/<slug>_scores.txt`.

Next backend: step 2 (oneshot also clears stale run files; brief is kept). Next game: step 1 (full clear).

## Staging helper

```bash
python generation/game_run_workflow.py files --step generation --game catan --backend codex
python generation/game_run_workflow.py files --step tests --game catan --backend codex
python generation/game_run_workflow.py files --step plot --game catan
```

Optional `--variant oneshot|agentic` limits staging to one variant.

## Generation commands

| Backend | Command |
|---------|---------|
| pi | `python generation/run_pi_series.py --game <game> --variant oneshot` then `agentic` |
| codex | `python generation/run_codex_series.py --game <game> --variant oneshot` then `agentic` |
| claude | notebook `run_generation()` in evaluation2.ipynb + evaluation.ipynb |

## Commit rules

- **Do** bundle oneshot + agentic for the same backend in one generation commit and one tests commit.
- **Never** commit judge packets (`*_judge_packet.md`).
- **Never** commit claude judge reviews (`*_judge_claude.md`) until explicitly re-enabled.
- **Never** add a separate clear-outputs commit — clearing is automatic after each plot pin and before each backend oneshot.
- After plot + commit, `outputs/` should hold at most the implementation brief (`.gitkeep` only between games).
- Space commit timestamps by real effort (generation > judges > plot).
- Scores survive in `plots/<slug>_pinned.json` + git history.

## See also

- `AGENTS.md` — artifact naming and flat `outputs/` policy
- `generation/game_run_workflow.py` — pin/plot/clear helpers
