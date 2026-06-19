# Current State

This file describes the repository as it exists today.
`README.md` describes the target state.

## Actual repository shape

```text
BoardBench/
├─ .pi/
│  └─ extensions/
│     └─ boardbench-context.ts
├─ AGENTS.md
├─ boardbench_checkliste.md
├─ boardbench_checkliste_einschaetzung.md
├─ CURRENT.md
├─ README.md
├─ requirements.txt
├─ TODO.md
├─ workflow_description.md
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
├─ code/
│  ├─ evaluation.ipynb
│  ├─ evaluation_draft.md
│  ├─ input/
│  │  ├─ game_rules.txt or game_rules.pdf
│  │  └─ prompt.txt
│  └─ outputs/
└─ exposé/
   └─ Bachelorarbeit_Exposé.pdf
```

## What is already in place

- a single prompt input file exists under `code/input/prompt.txt`
- the rules input file can be `code/input/game_rules.txt` or `code/input/game_rules.pdf`
- an outputs folder exists under `code/outputs/`
- a `requirements.txt` file exists for the Python notebook workflow, including `pypdf` for PDF rulebooks
- the evaluation notebook exists under `code/evaluation.ipynb`
- the notebook now keeps game, model, timeout, and output settings directly inside the notebook
- the notebook automatically uses the single supported `game_rules` file in `code/input/`, either `.txt` or `.pdf`
- the notebook has an optional generated-result check cell that runs `checks/run_checks.py`
- the prompt now asks for a slightly stricter minimal game API and stable action names
- the notebook is set up for the `Python (boardbench)` kernel on Python 3.12.3
- OpenSpiel is installed in the `boardbench` Python 3.12.3 environment
- a project-local pi extension exists under `.pi/extensions/boardbench-context.ts`
- a usage guide for that extension exists in `workflow_description.md`
- `TODO.md` tracks follow-up ideas for improving generation inputs and comparing prompting modes
- the repo now explicitly distinguishes between target state (`README.md`) and actual state (`CURRENT.md`)

## Main deviations from the target state

- the working folders are still nested under `code/`
- there are no root-level `inputs/`, `outputs/`, or `prompts/` folders yet
- the checks folder exists for generated-result checks, including result presence, Python syntax, startup, API, random rollout, and optional OpenSpiel comparison checks
- the evaluation notebook is still inside `code/`
- `code/evaluation_draft.md` currently holds a broad draft of possible evaluation rules
- there is no automated benchmark pipeline yet

## Current work packages

The current build phase is mainly about:

1. pipeline design
2. system prompts
3. output design
4. evaluation rules for generated output
5. pilot game selection

## Current workflow

Today, the repository is best understood as a staging version of the target workflow:

1. store the prompt text in `code/input/prompt.txt`
2. store the game rules in exactly one of `code/input/game_rules.txt` or `code/input/game_rules.pdf`
3. create or activate a Python 3.12.3 environment and install `requirements.txt`
4. update the game, model, timeout, and output variables directly in `code/evaluation.ipynb`
5. save raw model output and extracted Python files in `code/outputs/`
6. run the minimal smoke tests in `code/evaluation.ipynb`
7. optionally run generated-result checks from the notebook or from the repo root with `python checks/run_checks.py`

## Local pi extension behavior

The local extension currently:

- defaults pi to authoring mode
- can switch into a restricted readonly workflow mode
- can switch into a restricted generation mode with writes limited to `code/outputs/` and `outputs/`
- keeps restricted tool access focused on BoardBench workflow files
- blocks bash, edit, and write in readonly mode
- blocks bash and edit in generation mode
- offers `/bb-start`, `/bb-readonly`, `/bb-generate`, `/bb-authoring`, and `/bb-status`
- `/bb-start` opens a fresh restricted generation session with a minimal prompt that reads `code/input/prompt.txt` and exactly one of `code/input/game_rules.txt` or `code/input/game_rules.pdf`, then writes `code/outputs/nine_mens_morris.py`

## Transition intention

The intended cleanup direction is still the minimal target layout from `README.md`:

- `inputs/`
- `outputs/`
- `prompts/`
- `requirements.txt`
- `evaluation.ipynb`

The current `code/` layout is acceptable for now, but it is a transitional structure rather than the intended end state.

Intermediate artifacts should continue to be preserved because they may later be needed for the thesis write-up and method discussion.
