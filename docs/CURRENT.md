# Current State

This file describes the repository as it exists today.
`README.md` describes the compact root layout and main workflow.

## Actual repository shape

```text
BoardBench/
├─ AGENTS.md
├─ README.md
├─ TODO.md
├─ evaluation.ipynb
├─ requirements.txt
├─ inputs/
│  └─ game_rules.txt or game_rules.pdf
├─ prompts/
│  └─ rulebook_to_python.txt
├─ outputs/
├─ checks/
│  ├─ README.md
│  ├─ common.py
│  ├─ check_01_result_file.py
│  ├─ check_02_python_syntax.py
│  ├─ check_03_startable_game.py
│  ├─ check_04_required_api.py
│  ├─ check_05_random_rollouts.py
│  ├─ check_99_openspiel_compare.py
│  └─ run_checks.py
├─ docs/
│  ├─ CURRENT.md
│  ├─ workflow_description.md
│  ├─ evaluation_draft.md
│  ├─ boardbench_checkliste.md
│  ├─ boardbench_checkliste_einschaetzung.md
│  └─ PROBLEME.txt
├─ exposé/
└─ .pi/extensions/
```

## What is already in place

- root-level `evaluation.ipynb`
- root-level `inputs/`, `prompts/`, `outputs/`, and `checks/`
- a prompt file at `prompts/rulebook_to_python.txt`
- a rules input file at `inputs/game_rules.txt` or `inputs/game_rules.pdf`
- generated artifacts under `outputs/`
- generated-result checks under `checks/`
- `pypdf` support for PDF rulebooks in `requirements.txt`
- a project-local pi extension under `.pi/extensions/boardbench-context.ts`
- repo-supporting notes under `docs/`

## Current workflow

1. store the prompt text in `prompts/rulebook_to_python.txt`
2. store the game rules in exactly one of `inputs/game_rules.txt` or `inputs/game_rules.pdf`
3. create or activate a Python 3.12.3 environment and install `requirements.txt`
4. update game, model, timeout, and output variables in `evaluation.ipynb`
5. save raw model output and extracted Python files in `outputs/`
6. run generated-result checks from the notebook or from the repo root with `python checks/run_checks.py`
7. use optional final OpenSpiel comparison with `python checks/run_checks.py --include-final`

## Checks

Normal checks verify:

1. result file exists
2. result is valid Python syntax
3. generated game imports and starts
4. required API methods are present
5. 100 capped random rollouts do not crash or produce invalid dead states

The optional final check compares against OpenSpiel when `pyspiel` is available.

## Notes

The old loose root notes have been moved into `docs/` to keep the project root focused on the main workflow files.
