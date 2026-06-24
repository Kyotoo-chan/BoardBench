# Local Extension Model Testing

This file explains the current BoardBench workflow with the project-local pi extension in `.pi/extensions/boardbench-context.ts`.

## Current workflow files

- `prompts/rulebook_to_python.txt`
- `prompts/open_spiel_backbone.md`
- exactly one of `inputs/game_rules.txt` or `inputs/game_rules.pdf`
- generated artifacts under `outputs/`
- generated-result checks under `checks/`
- agentic notebook at `evaluation.ipynb`
- one-shot notebook at `evaluation2.ipynb`

## Notebook environment

```bash
conda create -n boardbench python=3.12.3 -y
conda activate boardbench
python -m pip install -r requirements.txt
```

Then open `evaluation.ipynb` for the agentic run or `evaluation2.ipynb` for the one-shot run.

If `inputs/game_rules.pdf` has no extractable text, the notebooks render it to page images under `inputs/rulebook_pages/` and pass those images to pi as rulebook attachments.

For the agentic run, the notebook creates a temporary isolated workspace containing only copied source material under `inputs/` and an `outputs/` folder for the generated file. The BoardBench `checks/` directory is not present in that workspace, so the generator can self-review syntax and logic without seeing the benchmark checks.

## Checks

Run normal generated-result checks from the notebook check cells, or from the repository root:

```bash
python checks/run_checks.py --game antichess --code-path outputs/antichess.py
```

Normal checks verify result existence, Python syntax, startup, required API, 1000 capped random rollouts without crashes or invalid dead states, and unambiguous normalized action names. Each check prints passed units and a normalized 0–1 score so implementations can be compared numerically.

Run one check:

```bash
python checks/run_checks.py --check 05_random_rollouts
```

Parse a saved LLM-judge score:

```bash
python checks/run_checks.py --include-judge --judge-path outputs/antichess_judge_gpt.md
```

This checks the machine-readable `score: 0.0-1.0` format. A low judge score is data, not a runner failure.

Run the pair action-language comparison after both generated variants exist:

```bash
python checks/compare_pair.py \
  --game antichess \
  --left-code-path outputs/antichess_oneshot.py \
  --right-code-path outputs/antichess_agentic.py
```

This comparison normalizes emitted action names only. It does not add missing legal actions.

Run the optional OpenSpiel comparison:

```bash
python checks/run_checks.py --include-final
```

The OpenSpiel comparison checks sampled current player, legal action set, apply step, and terminal returns when both sides are terminal. It does not compare render strings or move speed. Reference-specific notation adapters, such as Havannah q/r coordinates to OpenSpiel point labels, live only in this optional final comparison.

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

- root workflow files: `README.md`, `AGENTS.md`, `TODO.md`, `requirements.txt`, `evaluation.ipynb`, `evaluation2.ipynb`
- `docs/`
- `inputs/`
- `prompts/`
- `outputs/`
- `checks/`
- `.pi/extensions/`
