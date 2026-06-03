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
├─ QUESTIONS.txt
├─ README.md
├─ requirements.txt
├─ workflow_description.md
├─ code/
│  ├─ evaluation.ipynb
│  ├─ evaluation_draft.md
│  ├─ input/
│  │  ├─ game_rules.txt
│  │  └─ prompt.txt
│  └─ outputs/
└─ exposé/
   └─ Bachelorarbeit_Exposé.pdf
```

## What is already in place

- a single prompt input file exists under `code/input/prompt.txt`
- a rules input file exists under `code/input/game_rules.txt`
- an outputs folder exists under `code/outputs/`
- a `requirements.txt` file exists for the Python notebook workflow
- the evaluation notebook exists under `code/evaluation.ipynb`
- the notebook now keeps game, model, timeout, and output settings directly inside the notebook
- the prompt now asks for a slightly stricter minimal game API and stable action names
- the notebook is set up for the `Python (boardbench)` kernel on Python 3.12.3
- OpenSpiel is installed in the `boardbench` Python 3.12.3 environment
- a project-local pi extension exists under `.pi/extensions/boardbench-context.ts`
- a usage guide for that extension exists in `workflow_description.md`
- the repo now explicitly distinguishes between target state (`README.md`) and actual state (`CURRENT.md`)

## Main deviations from the target state

- the working folders are still nested under `code/`
- there are no root-level `inputs/`, `outputs/`, or `prompts/` folders yet
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
2. store the game rules in `code/input/game_rules.txt`
3. create or activate a Python 3.12.3 environment and install `requirements.txt`
4. update the game, model, timeout, and output variables directly in `code/evaluation.ipynb`
5. save raw model output and extracted Python files in `code/outputs/`
6. run the minimal smoke tests in `code/evaluation.ipynb`
7. track unresolved issues in `QUESTIONS.txt`

## Local pi extension behavior

The local extension currently:

- defaults pi to authoring mode
- can switch into a restricted readonly workflow mode
- keeps readonly tool access focused on BoardBench workflow files
- blocks bash only in readonly mode
- offers `/bb-readonly`, `/bb-generate`, `/bb-authoring`, and `/bb-status`

## Transition intention

The intended cleanup direction is still the minimal target layout from `README.md`:

- `inputs/`
- `outputs/`
- `prompts/`
- `requirements.txt`
- `evaluation.ipynb`
- `QUESTIONS.txt`

The current `code/` layout is acceptable for now, but it is a transitional structure rather than the intended end state.

Intermediate artifacts should continue to be preserved because they may later be needed for the thesis write-up and method discussion.
