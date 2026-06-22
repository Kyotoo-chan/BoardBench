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
├─ evaluation2.ipynb
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
- `prompts/` – reusable prompt text, including generation, implementation-brief, OpenSpiel-inspired backbone, and LLM-judge prompts
- `outputs/` – raw model responses, generated Python files, references, and preserved artifacts
- `checks/` – result checks for generated Python game files
- `docs/` – workflow notes, checklists, current-state notes, LLM-judge workflow notes, drafts, and problem notes
- `evaluation.ipynb` – agentic manual generation/evaluation notebook
- `evaluation2.ipynb` – one-shot comparison notebook
- `TODO.md` – follow-up ideas to investigate
- `requirements.txt` – local Python dependencies
- `AGENTS.md` – coding-agent instructions

## Minimal workflow

1. Put the rulebook into `inputs/game_rules.txt` or `inputs/game_rules.pdf`; image-only PDFs are rendered to page images by the notebooks.
2. Optionally create an implementation brief with `prompts/rulebook_to_implementation_brief.md`.
3. Keep the generation prompt in `prompts/rulebook_to_python.txt`.
4. Optionally add `prompts/open_spiel_backbone.md` as extra LLM context.
5. Set game/model/output variables in `evaluation.ipynb` for the agentic run and `evaluation2.ipynb` for the one-shot run.
6. Generate one self-contained Python module from the provided rules only.
7. Save the raw response and extracted `.py` file in `outputs/`.
8. Run the generated-result checks from the notebooks or with `python checks/run_checks.py`; each check reports a normalized 0–1 score.
9. Use the pair action-language comparison when both generated variants exist; it normalizes emitted action names only and does not add moves.
10. Optionally run an LLM judge check with `prompts/llm_judge_review.md`, save it in `outputs/`, and validate it with `python checks/run_checks.py --include-judge`.
11. Preserve notes and artifacts that may matter for the thesis write-up.

## Notes

- The repository is intentionally small and manual-first.
- Use `docs/CURRENT.md` for the current detailed repo state.
- Use `docs/workflow_description.md` for the local pi extension workflow.
