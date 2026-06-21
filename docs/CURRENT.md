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
│  ├─ open_spiel_base_backbone.md
│  ├─ open_spiel_game_type_backbones.md
│  └─ llm_judge_review.md
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
- OpenSpiel-inspired prompt backbones at `prompts/open_spiel_base_backbone.md` and `prompts/open_spiel_game_type_backbones.md`
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
3. optionally add `prompts/open_spiel_base_backbone.md` and the relevant game-type profile as extra LLM context
4. store the game rules in exactly one of `inputs/game_rules.txt` or `inputs/game_rules.pdf`
5. create or activate a Python 3.12.3 environment and install `requirements.txt`
6. update game, model, timeout, and output variables in `evaluation.ipynb`
7. save raw model output and extracted Python files in `outputs/`
8. run generated-result checks from the notebook or from the repo root with `python checks/run_checks.py`
9. use optional final OpenSpiel comparison with `python checks/run_checks.py --include-final`
10. optionally run an LLM judge review with `prompts/llm_judge_review.md` and save the raw review in `outputs/`

## Checks

Normal checks verify:

1. result file exists
2. result is valid Python syntax
3. generated game imports and starts
4. required API methods are present
5. 100 capped random rollouts do not crash or produce invalid dead states

The optional final check compares against OpenSpiel when `pyspiel` is available.

The LLM-as-judge review is a manual qualitative check for now, documented in `docs/llm_judge_workflow.md`. It should not introduce provider/API-key automation until that is explicitly needed.

## Notes

The old loose root notes have been moved into `docs/` to keep the project root focused on the main workflow files.
