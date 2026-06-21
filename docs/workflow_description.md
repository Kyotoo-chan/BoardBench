# Local Extension Model Testing

This file explains the current BoardBench workflow with the project-local pi extension in `.pi/extensions/boardbench-context.ts`.

## Current workflow files

- `prompts/rulebook_to_python.txt`
- `prompts/open_spiel_backbone.md`
- exactly one of `inputs/game_rules.txt` or `inputs/game_rules.pdf`
- generated artifacts under `outputs/`
- generated-result checks under `checks/`
- notebook at `evaluation.ipynb`

## Notebook environment

```bash
conda create -n boardbench python=3.12.3 -y
conda activate boardbench
python -m pip install -r requirements.txt
```

Then open `evaluation.ipynb`.

## Checks

Run normal generated-result checks from the `Checks` cell in `evaluation.ipynb`, or from the repository root:

```bash
python checks/run_checks.py --game antichess --code-path outputs/antichess.py
```

Normal checks verify result existence, Python syntax, startup, required API, and 1000 capped random rollouts without crashes or invalid dead states.

Run one check:

```bash
python checks/run_checks.py --check 05_random_rollouts
```

Check a saved LLM-judge review:

```bash
python checks/run_checks.py --include-judge --judge-path outputs/antichess_judge_gpt.md
```

Run the optional OpenSpiel comparison:

```bash
python checks/run_checks.py --include-final
```

The OpenSpiel comparison checks sampled current player, legal action set, apply step, and terminal returns when both sides are terminal. It does not compare render strings or move speed.

## Local extension commands

Inside pi:

```text
/bb-status
/bb-start
/bb-readonly
/bb-generate
/bb-authoring
```

- `/bb-start` creates a fresh restricted generation session and pre-fills the minimal prompt.
- `/bb-readonly` keeps the session in restricted read-only mode.
- `/bb-generate` enables restricted generation mode with output writes only.
- `/bb-authoring` enables editing and bash across the repo.
- `/bb-status` shows the current mode.

## Minimal fresh generation session

Inside pi, run:

```text
/bb-start
```

The prefilled prompt reads only:

- `prompts/rulebook_to_python.txt`
- `inputs/game_rules.txt` or `inputs/game_rules.pdf`

and writes the generated file under `outputs/`.

## One-shot print-mode example

```bash
pi -p --model <provider/model> \
  @prompts/rulebook_to_python.txt \
  @inputs/game_rules.txt \
  "Use the provided files only and generate the Python module."
```

Use `@inputs/game_rules.pdf` instead when the rulebook is stored as PDF.

## Allowed restricted workflow paths

The local extension allowlist includes:

- root workflow files: `README.md`, `AGENTS.md`, `TODO.md`, `requirements.txt`, `evaluation.ipynb`
- `docs/`
- `inputs/`
- `prompts/`
- `outputs/`
- `checks/`
- `.pi/extensions/`
