# Claude generation workflow

BoardBench can run LLM steps through **Claude Code CLI** (`claude -p`) using your Claude subscription login, with the same notebook flow as the old `pi` + GPT runs.

Evaluation (checks, OpenSpiel compare) still runs locally. LLM steps are:

- generation (oneshot + agentic)
- LLM judge
- action-language align (single + pair)

## Notebook settings

In the setup cell of `evaluation.ipynb` and `evaluation2.ipynb`:

```python
LLM_BACKEND = "claude"  # default
LLM_MODEL = "opus"
LLM_EFFORT = "max"      # comparable to former gpt-5.5:xhigh runs
```

Other backends:

| Backend | Behavior |
|---------|----------|
| `claude` | `claude -p` subprocess via subscription login |
| `pi` | legacy local `pi -p` workflow |
| `manual` | write generation packet only; paste answer yourself |

## Prerequisites

1. `conda` env `boardbench` with `pip install -r requirements.txt`
2. `npm install` in repo root (local `claude` CLI at `node_modules/.bin/claude`)
3. `claude auth login` once; verify with `claude auth status --text`
4. Unset `ANTHROPIC_API_KEY` for subscription billing

The setup cell calls `generation.notebook_bootstrap.bootstrap_notebook()`, which activates the archived rulebook, checks Claude auth, and generates a missing implementation brief when the game catalog requests one. Generation and judge steps use a **2 hour** timeout each.

## Normal workflow (like before)

### Oneshot — `evaluation2.ipynb`

1. Run setup cell (set `GAME`)
2. Run bootstrap cell (`bootstrap_notebook` — rulebook, Claude auth, optional brief)
3. Run generation cell (`run_generation()`)
4. Run evaluation cell (`run_full_evaluation(...)`)

### Agentic — `evaluation.ipynb`

1. Run setup cell (set `GAME`)
2. Run bootstrap cell (`bootstrap_notebook` — rulebook, Claude auth, optional brief)
3. Run generation cell (`run_generation()`)
4. Run evaluation cell (`run_full_evaluation(...)`)
5. After both variants exist: pair compare cell

No manual ingest step is needed when `LLM_BACKEND = "claude"`.

## What the CLI call looks like

Implemented in `generation/llm_cli.py`:

- oneshot / judge / align: `claude -p --tools ""` plus `--disallowedTools` for align (Read only when PDF page attachments are needed)
- agentic generation: `claude -p --model opus --effort max --permission-mode bypassPermissions` in an isolated temp workspace
- image-only PDFs: `--tools Read` plus `--add-dir` for rendered page folders

Raw answers are saved to `outputs/<game>_<variant>.md`; extracted code to `outputs/<game>_<variant>.py`.

## Manual fallback

Set `LLM_BACKEND = "manual"` only if you want to run Claude in the IDE chat yourself:

1. `run_generation()` writes `outputs/<game>_<variant>_generation_packet.md`
2. save Claude's answer to `outputs/<game>_<variant>.md`
3. `ingest_generation_response()`

Judge/align still require `LLM_BACKEND = "claude"` or `"pi"` for automated notebook runs.

## Per-game rulebooks

Archived inputs:

```text
inputs/games/havannah/game_rules.pdf
inputs/games/abalone/game_rules.pdf
inputs/games/exploding_kittens/game_rules.pdf
```

Activate one game:

```bash
python generation/activate_game.py havannah
```

See `docs/claude_rerun_series.md` for the full three-game rerun order.
