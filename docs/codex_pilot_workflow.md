# Codex pilot rerun

Side branch experiment: regenerate all six pi-era implementations (Havannah, Abalone, Exploding Kittens × oneshot/agentic) with **OpenAI Codex CLI** instead of `pi -p`.

## Prerequisites

- `npx @openai/codex exec` works (`codex ok` smoke test)
- Codex logged in via your usual OpenAI/Codex auth
- `boardbench` conda env for checks

## Run

```bash
python generation/activate_game.py havannah   # optional; script activates per game
python generation/run_codex_series.py --game havannah --variant oneshot
python generation/run_codex_series.py --all
```

Defaults mirror the old pi pilot: model `gpt-5.5`, effort `xhigh`, same prompts/notebooks, base checks 01–06 after each generation (no judge in the automated runner).

For judge and OpenSpiel compare, run after generation:

```bash
python generation/run_codex_eval.py --game havannah --variant oneshot
python generation/run_codex_eval.py --all   # every game with outputs/<game>_<variant>.py
```

## Outputs policy (one active game)

`outputs/` should contain **only the current game** being worked on. Older games stay in git history.

Canonical codex artifacts per variant (pattern `{game}_{backend}_{variant}`):

| File | Example |
|------|---------|
| raw response | `expl_codex_os.md` |
| extracted module | `expl_codex_ag.py` |
| check log | `expl_codex_os_checks.txt` |
| judge review | `expl_codex_os_judge.md` |
| judge packet | `expl_codex_ag_judge_packet.md` |

Short slugs: game `hav|aba|expl`, backend `gpt|claude|codex`, variant `os|ag`.

Havannah OpenSpiel also writes `*_pre_align.py` and `*_action_align.md`.

Do **not** keep in `outputs/`: `*_generation_packet.md` (Claude-only), `*_first_gen.*`, `*_pi_rerun_*`, or temp `boardbench_*_codex_*.md` files.

Recover a previous game from history:

```bash
git checkout 258e505 -- outputs/havannah_oneshot.py outputs/havannah_oneshot.md
```

Cross-backend comparison plots pin GPT/Claude/Codex scores in `plots/make_plots.py` (not read live from `outputs/`).

## Suggested git rhythm

Match `docs/claude_rerun_series.md`:

1. `prepare <game> rulebook and clear <previous> outputs`
2. `save <game> codex oneshot generation`
3. `save <game> codex agentic generation`
4. `save <game> codex test artifacts` (judge + updated checks)

## Compare against pi / Claude

| Backend | Invocation |
|---------|------------|
| pi (GPT era) | `pi -p --model openai-codex/gpt-5.5:xhigh` |
| Claude rerun | `claude -p` in notebooks |
| Codex direct | `npx @openai/codex exec` via `generation/run_codex_series.py` |

Compare weighted summary scores from committed `*_checks.txt` logs and `plots/*_scores.txt`.
