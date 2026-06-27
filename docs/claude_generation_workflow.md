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

1. Install Claude Code CLI (`claude` on PATH)
2. Log in once: `claude auth login`
3. Verify: `claude auth status --text`
4. Use the `boardbench` conda env for checks (`requirements.txt`)

Important billing note: if `ANTHROPIC_API_KEY` is set in your shell, Claude Code may bill API usage instead of your subscription. Unset it for subscription-based runs.

## Normal workflow (like before)

### Oneshot — `evaluation2.ipynb`

1. Run setup cell (`GAME`, `RUN_VARIANT = "oneshot"`)
2. `run_generation()`
3. `run_full_evaluation(...)`

### Agentic — `evaluation.ipynb`

1. Run setup cell (`GAME`, `RUN_VARIANT = "agentic"`)
2. `run_generation()`
3. `run_full_evaluation(...)`
4. After both variants exist: pair compare cell

No manual ingest step is needed when `LLM_BACKEND = "claude"`.

## What the CLI call looks like

Implemented in `generation/llm_cli.py`:

- oneshot / judge / align: `claude -p --tools ""` plus `--disallowedTools` for align (Read only when PDF page attachments are needed)
- agentic generation: `claude -p --model opus --effort max --permission-mode bypassPermissions` in an isolated temp workspace
- image-only PDFs: `--tools Read` plus `--add-dir` for rendered page folders

Raw answers are saved to `outputs/<game>_<variant>.md`; extracted code to `outputs/<game>_<variant>.py`.

## Manual fallback

Set `LLM_BACKEND = "manual"` only if you want to run Claude in the Cursor chat yourself:

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
