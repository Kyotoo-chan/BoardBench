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
├─ CURRENT.md
├─ QUESTIONS.txt
├─ README.md
├─ workflow_description.md
├─ code/
│  ├─ compare_to_openspiel.ipynb
│  ├─ evaluation_draft.md
│  ├─ input_rules/
│  │  └─ rules.txt
│  ├─ outputs/
│  └─ prompts/
│     ├─ game_to_python.md
│     └─ system.md
└─ exposé/
   └─ Bachelorarbeit_Exposé.pdf
```

## What is already in place

- reusable prompt files exist under `code/prompts/`
- an input rules folder exists under `code/input_rules/`
- an outputs folder exists under `code/outputs/`
- the comparison notebook exists under `code/compare_to_openspiel.ipynb`
- the notebook already points to `code/outputs/`
- a project-local pi extension exists under `.pi/extensions/boardbench-context.ts`
- a usage guide for that extension exists in `workflow_description.md`
- the repo now explicitly distinguishes between target state (`README.md`) and actual state (`CURRENT.md`)

## Main deviations from the target state

- the working folders are still nested under `code/`
- there are no root-level `inputs/`, `outputs/`, or `prompts/` folders yet
- the comparison notebook is still inside `code/`
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

1. store rule text in `code/input_rules/`
2. use `code/prompts/system.md` and `code/prompts/game_to_python.md`
3. save raw model output and extracted Python files in `code/outputs/`
4. compare files in `code/compare_to_openspiel.ipynb`
5. track unresolved issues in `QUESTIONS.txt`

## Local pi extension behavior

The local extension currently:

- defaults pi to a readonly workflow mode
- keeps tool access focused on BoardBench workflow files
- blocks bash
- offers `/bb-readonly`, `/bb-authoring`, and `/bb-status`

## Transition intention

The intended cleanup direction is still the minimal target layout from `README.md`:

- `inputs/`
- `outputs/`
- `prompts/`
- `compare_to_openspiel.ipynb`
- `QUESTIONS.txt`

The current `code/` layout is acceptable for now, but it is a transitional structure rather than the intended end state.

Intermediate artifacts should continue to be preserved because they may later be needed for the thesis write-up and method discussion.
