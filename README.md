# BoardBench

BoardBench is a bachelor thesis repository for experimenting with board-game rulebooks, LLM-generated Python game environments, and later comparisons against OpenSpiel references.

## Clean repository layout

The root is kept intentionally small:

```text
BoardBench/
├─ AGENTS.md
├─ README.md
├─ TODO.md
├─ evaluation.ipynb
├─ requirements.txt
├─ inputs/
├─ prompts/
├─ outputs/
├─ checks/
├─ docs/
├─ exposé/
└─ .pi/
```

## What goes where

- `inputs/` – current rulebook input as `game_rules.txt` or `game_rules.pdf`
- `prompts/` – reusable prompt text, currently `rulebook_to_python.txt`
- `outputs/` – raw model responses, generated Python files, references, and preserved artifacts
- `checks/` – result checks for generated Python game files
- `docs/` – workflow notes, checklists, current-state notes, drafts, and problem notes
- `evaluation.ipynb` – manual generation/evaluation notebook
- `TODO.md` – follow-up ideas to investigate
- `requirements.txt` – local Python dependencies
- `AGENTS.md` – coding-agent instructions

## Minimal workflow

1. Put the rulebook into `inputs/game_rules.txt` or `inputs/game_rules.pdf`.
2. Keep the generation prompt in `prompts/rulebook_to_python.txt`.
3. Set game/model/output variables in `evaluation.ipynb`.
4. Generate one self-contained Python module from the provided rules only.
5. Save the raw response and extracted `.py` file in `outputs/`.
6. Run the generated-result checks from the notebook or with `python checks/run_checks.py`.
7. Preserve notes and artifacts that may matter for the thesis write-up.

## Notes

- The repository is intentionally small and manual-first.
- Use `docs/CURRENT.md` for the current detailed repo state.
- Use `docs/workflow_description.md` for the local pi extension workflow.
