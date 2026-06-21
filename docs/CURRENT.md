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
│  ├─ rulebook_to_python.txt
│  ├─ rulebook_to_implementation_brief.md
│  ├─ open_spiel_backbone.md
│  └─ llm_judge_review.md
├─ outputs/
├─ checks/
│  ├─ common.py
│  ├─ 01_result_file.py
│  ├─ 02_python_syntax.py
│  ├─ 03_startable_game.py
│  ├─ 04_required_api.py
│  ├─ 05_random_rollouts.py
│  ├─ 90_llm_judge.py
│  ├─ 99_openspiel_compare.py
│  └─ run_checks.py
├─ docs/
│  ├─ CURRENT.md
│  ├─ workflow_description.md
│  ├─ evaluation_draft.md
│  ├─ boardbench_checkliste.md
│  ├─ boardbench_checkliste_einschaetzung.md
│  ├─ open_spiel_environment_patterns.md
│  ├─ llm_judge_workflow.md
│  └─ PROBLEME.txt
├─ exposé/
└─ .pi/extensions/
```

## What is already in place

- root-level `evaluation.ipynb`
- root-level `inputs/`, `prompts/`, `outputs/`, and `checks/`
- a prompt file at `prompts/rulebook_to_python.txt`
- an OpenSpiel-inspired prompt backbone at `prompts/open_spiel_backbone.md`
- an implementation-brief prompt at `prompts/rulebook_to_implementation_brief.md`
- an LLM-judge review prompt at `prompts/llm_judge_review.md`
- OpenSpiel environment pattern notes at `docs/open_spiel_environment_patterns.md`
- LLM-as-judge workflow notes at `docs/llm_judge_workflow.md`
- a rules input file at `inputs/game_rules.txt` or `inputs/game_rules.pdf`
- generated artifacts under `outputs/`
- generated-result checks under `checks/`
- `pypdf` support for PDF rulebooks in `requirements.txt`
- a project-local pi extension under `.pi/extensions/boardbench-context.ts`
- repo-supporting notes under `docs/`

## Current workflow

1. store the prompt text in `prompts/rulebook_to_python.txt`
2. optionally create an implementation brief with `prompts/rulebook_to_implementation_brief.md`
3. optionally add `prompts/open_spiel_backbone.md` as extra LLM context
4. store the game rules in exactly one of `inputs/game_rules.txt` or `inputs/game_rules.pdf`
5. create or activate a Python 3.12.3 environment and install `requirements.txt`
6. update game, model, timeout, and output variables in `evaluation.ipynb`
7. save raw model output and extracted Python files in `outputs/`
8. run generated-result checks from the notebook or from the repo root with `python checks/run_checks.py`
9. use optional final OpenSpiel comparison with `python checks/run_checks.py --include-final`
10. optionally run an LLM judge review with `prompts/llm_judge_review.md`, save it in `outputs/`, and validate it with `python checks/run_checks.py --include-judge`

## Checks

Normal checks verify:

1. result file exists
2. result is valid Python syntax
3. generated game imports and starts
4. required API methods are present
5. 1000 capped random rollouts do not crash or produce invalid dead states

The optional `90_llm_judge.py` check validates a saved LLM-judge review verdict.
The optional final OpenSpiel check compares sampled states against OpenSpiel when `pyspiel` is available: current player, legal action set, apply step, and terminal returns when both sides are terminal. It does not compare render strings or move speed.

The LLM-as-judge review is a manual qualitative check for now, documented in `docs/llm_judge_workflow.md`. It should not introduce provider/API-key automation until that is explicitly needed.

## Notes

The old loose root notes have been moved into `docs/` to keep the project root focused on the main workflow files.
