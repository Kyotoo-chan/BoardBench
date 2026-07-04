# Claude rerun series — three pilot games

Re-implement **Havannah → Abalone → Exploding Kittens**, each with **oneshot** and **agentic**, using Claude for generation.

Previous pilot artifacts used `pi` + `openai-codex/gpt-5.5:xhigh`. This series keeps prompts, checks, and scoring comparable but swaps the generation backend to Claude.

## Game catalog

| Order | Slug | OpenSpiel compare | Implementation brief | Archived rules |
|------:|------|-------------------|------------------------|----------------|
| 1 | `havannah` | yes (`havannah(board_size=8)`) | recommended | `inputs/games/havannah/game_rules.pdf` |
| 2 | `abalone` | no | recommended (figures!) | `inputs/games/abalone/game_rules.pdf` |
| 3 | `exploding_kittens` | no | recommended | `inputs/games/exploding_kittens/game_rules.pdf` |

Activate a game before each block:

```bash
python generation/activate_game.py <slug>
```

Then set `GAME = "<slug>"` and `OPEN_SPIEL_GAME` / `INCLUDE_OPENSPIEL_COMPARE` in both notebooks (or use the prepared values after the per-game prep commit).

## Per-game workflow

For each game:

### A. Oneshot

1. `evaluation2.ipynb`: `RUN_VARIANT = "oneshot"`, `LLM_BACKEND = "claude"`.
2. `run_generation()` then `run_full_evaluation(...)`.
4. Git commit: generation artifacts + check log (+ notebook outputs if intentional test commit).

### B. Agentic

1. `evaluation.ipynb`: `RUN_VARIANT = "agentic"`, `LLM_BACKEND = "claude"`.
2. `run_generation()` then `run_full_evaluation(...)`.
4. Git commit: generation + evaluation artifacts.

### C. Pair compare (after both variants exist)

1. `evaluation.ipynb` pair cell only.
2. Expect lockstep compare to work best for placement games (Havannah). Card games may diverge in action enumeration — still record the result.

## Suggested git commit rhythm

Match existing repo style (lowercase, step-by-step):

1. `prepare <game> rulebook and clear <previous> outputs`
2. `save <game> generations` (oneshot + agentic in one commit)
3. `save <game> test artifacts`

Do **not** squash intermediate experiment commits.

## Evaluation defaults

| Game | `INCLUDE_OPENSPIEL_COMPARE` (agentic notebook) | Notes |
|------|-----------------------------------------------|-------|
| Havannah | `True` | calibrates against OpenSpiel |
| Abalone | `False` | no OS game in catalog |
| Exploding Kittens | `False` | card game |

Keep `ROLLOUTS = 100` for manual runs unless you intentionally want a heavier check.

## Current series position

- **Active game:** `havannah`
- **Next step:** Havannah oneshot generation via Claude in `evaluation2.ipynb`

Update this section as you progress through the series.
