# BoardBench

BoardBench is a bachelor thesis repository that explores a board-game analogue of OpenAI's PaperBench.

Instead of scientific papers, the source material here is **board-game rulebooks**. The central question is how well LLMs can turn those rules into usable **Python game environments**.

## Vision

The long-term goal is to build a simple and reproducible workflow that can:

1. take a rulebook as the only source of truth
2. generate a Python game environment with an LLM
3. compare that result against an OpenSpiel reference where available
4. define reusable evaluation rules for the generated output
5. later test broader sets of games with the same benchmark logic

OpenSpiel is the first reference layer, not necessarily the final scope.

## Current focus

The repository is still in the workflow-building phase.

Current work packages:

1. pipeline design
2. system prompts
3. output design
4. evaluation rules for generated output
5. pilot game selection

The goal right now is not a full benchmark framework yet, but a good foundation for later experiments and the final written thesis.

## Target repository shape

```text
BoardBench/
├─ inputs/
├─ outputs/
├─ prompts/
├─ compare_to_openspiel.ipynb
├─ CURRENT.md
├─ workflow_description.md
├─ QUESTIONS.txt
├─ AGENTS.md
├─ README.md
├─ exposé/
└─ .pi/
   └─ extensions/
      └─ boardbench-context.ts
```

## What goes where

- `inputs/` – rulebooks or extracted rule text
- `outputs/` – raw model responses, extracted Python files, reference files, and other intermediate artifacts
- `prompts/` – reusable prompts for rulebook-to-Python runs
- `compare_to_openspiel.ipynb` – manual comparison notebook
- `CURRENT.md` – current repo state and deviations from the target layout
- `workflow_description.md` – how to test the workflow with pi and the local extension
- `QUESTIONS.txt` – append-only list of open research questions and problems
- `AGENTS.md` – instructions for coding agents working in this repo
- `.pi/extensions/boardbench-context.ts` – optional project-local pi extension for restricted workflow tests

## What should always be preserved

Because this repository supports a bachelor thesis, intermediate results matter.

Keep at least:

- the raw model response
- the extracted Python file
- important assumptions or unresolved ambiguities
- comparison notes or observations that may matter later for the written analysis

## Minimal workflow

1. put a rulebook or extracted rule text into `inputs/`
2. use `prompts/system.md` and `prompts/game_to_python.md`
3. generate one self-contained Python module from the provided rules only
4. save the full raw answer in `outputs/`
5. save the extracted `.py` file separately in `outputs/`
6. compare the result later in `compare_to_openspiel.ipynb`
7. record open questions in `QUESTIONS.txt`

## Notes

- `README.md` describes the intended target state and overall thesis direction.
- `CURRENT.md` describes the repository as it actually exists today.
- `workflow_description.md` describes the local pi testing workflow.
- The current repo is intentionally small and manual-first.
