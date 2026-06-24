# AGENTS.md

## Purpose of this repository

This repository supports a bachelor thesis workflow around **board game rulebooks**, **LLM-generated Python game environments**, and later **comparisons against OpenSpiel references**.

The current repo focus is **repo building and experiment preparation**, not yet automated benchmarking.

## Long-term direction

The broader thesis goal is to build a board-game benchmark idea inspired by PaperBench:

- start from a board-game rulebook as source material
- generate a Python game environment with an LLM
- compare against OpenSpiel where possible
- later derive more general evaluation rules across games

Coding agents should therefore optimize for:

- a reusable and understandable workflow
- prompts and outputs that are easy to compare later
- preservation of intermediate artifacts useful for the final written thesis

## Scope for coding agents

Coding agents working in this repository should primarily help with:

- keeping the repository structure simple and understandable
- improving the manual workflow from rulebook to Python output
- maintaining reusable prompts and documentation
- preserving artifacts needed for later comparison
- preparing, but not overengineering, future benchmark steps

This file is for **general coding agents that help build the repo**.
It is **not** the specification for later gameplay agents or benchmark agents.

## Current workflow philosophy

Prefer the smallest useful setup:

- one `inputs/` folder
- one `outputs/` folder
- one `prompts/` folder
- one lightweight `checks/` folder for small runnable checks of generated results
- one `docs/` folder for secondary notes, drafts, checklists, and current-state details
- root-level evaluation notebooks for agentic and one-shot comparison runs

Avoid introducing large frameworks, provider abstractions, or complex evaluation pipelines unless explicitly requested.

## Hard rules

1. Keep the repository minimal unless the user asks for more structure.
2. Do not silently introduce API-key based workflows when the current task is subscription-first/manual.
3. Do not assume external game knowledge if the task says to rely only on the provided rulebook/text.
4. Keep raw model outputs whenever the workflow touches model generations.
5. Do not delete or rewrite `QUESTIONS.txt` automatically; it is user-maintained.
6. Prefer readable files and explicit documentation over hidden magic.
7. Call out deviations from the agreed plan explicitly.
8. When the user specifies commit times, use explicit `hh:mm:ss` timestamps and do not use `00` seconds.
9. When writing commit messages, keep them lowercase and stylistically close to the existing short commit history.
10. If a task is split into multiple commits, space the commit timestamps according to the rough effort split, and set the final commit to the current time unless the user says otherwise.
11. When estimating commit spacing, count planning, thinking, and deciding time as part of the work, not only the file editing time.
12. Keep code changes minimal and focused unless the user explicitly asks for a broader refactor.
13. Use the `boardbench` Conda environment for Python commands, checks, notebook smoke tests, and dependency validation. In Git Bash, use `/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench ...` when `conda` is not on PATH.

## Git history and commit workflow

This repository uses git history as part of the thesis workflow record, not only as a deployment log.

- **Preserve step-by-step commits.** Keep separate commits for distinct workflow phases such as repo setup, generation, check runs, judge runs, fixes, calibration, and switching to a new game.
- **Do not squash, soft-reset, or rewrite away intermediate commits** unless the user explicitly asks for history rewriting.
- **Do not collapse diverged local/remote histories into one commit** when the user asks to "clean up the graph". In that case, prefer restoring/replacing the remote branch with the user's intentional local commit chain (`git push --force-with-lease`) instead of deleting intermediate commits.
- When the user asks to remove old `outputs/` files for a new game, delete them in a **new commit** only. Do not assume earlier experiment commits should disappear from history; they remain part of the recorded workflow.
- Match the existing short lowercase commit style and split commits by meaningful experiment steps rather than by arbitrary file batches.
- When the user specifies commit times, keep the existing spacing rules in the hard rules above.

## Coding style expectations

When adding code to this repo, prefer:

- plain Python
- standard library first
- simple file layouts
- self-contained modules where possible
- readable names and comments
- explicit assumptions when information is missing

Avoid:

- unnecessary dependencies
- complex abstractions too early
- hidden background automation
- overfitting the repo to one provider or one model

## Documentation expectations

When creating or updating workflow files:

- explain what a file is for
- keep instructions short and actionable
- make manual steps reproducible where possible
- preserve the distinction between:
  - repo-building support
  - later gameplay/benchmark evaluation

## Output conventions

If a workflow produces model artifacts, prefer storing:

- the raw answer from the model
- the extracted Python file
- any important assumptions or unresolved issues

Use simple, human-readable filenames.

## Artifact and path rules

- `outputs/` holds generated game code, raw LLM answers, check logs, judge reviews, align backups, and other experiment artifacts needed for later thesis analysis.
- **Do not gitignore `outputs/`** or hide generated artifacts to make `git status` look clean.
- Commit `outputs/` artifacts when they belong to an intentional experiment run the user wants preserved.
- Rendered PDF rulebook page images belong under `inputs/rulebook_pages/`, never `outputs/rulebook_pages/`.
- Judge packets and pi attachments should reference `inputs/rulebook_pages/` paths for page images.
- Notebook cell execution output complements `outputs/` text logs. For intentional test or experiment commits, **keep** the relevant notebook stdout (`OK` / `FAIL` / `---- summary` lines and per-phase run times) so the saved run is visible without re-execution.
- Clear only stale or noisy notebook outputs before commit (unrelated cells, huge tracebacks, admin noise). Do **not** strip outputs from cells that belong to the committed test run.
- Mirror important notebook results in `outputs/` where applicable (e.g. `*_checks.txt`, `*_pair_action_compare.txt`).

## Evaluation notebook rules

- `evaluation.ipynb` = agentic run; `evaluation2.ipynb` = oneshot run.
- Pair action-language comparison belongs only in `evaluation.ipynb`, not `evaluation2.ipynb`.
- `run_full_evaluation()` is the one-cell full pipeline when the user wants everything at once.
- Pipeline order: base checks (01–06) → LLM judge → **only** `90_llm_judge` → action-language align → **only** `99_openspiel_compare`.
- Never re-run the full base-check suite after the judge step.
- Print **one** aggregated `---- summary` line at the very end; intermediate phases use `--no-summary`.
- On check failures, continue through judge and OpenSpiel phases when enabled; raise only at the end with the list of failed phases.
- During iterative development, keep notebook output minimal: stream only `OK` / `FAIL` / final `summary` lines, no admin prints (`running checks`, `Saved check log`, `CompletedProcess`, etc.).
- For intentional test-run commits, preserve those same minimal result lines **with timings** in the executed notebook cells and matching `outputs/` logs.
- Checks report normalized `passed/total` unit scores per check line. The final `---- summary` score is a **weighted average of per-check scores**, not a raw sum of all units. Smoke checks `01`–`04` weight 1 each; quality checks (`05`, `06`, `90`, `99`, pair compare) weight 10 each and count equally among themselves.
- Rollout, action-language, and pair-comparison checks keep running after failures and score proportionally within each check (for example `987/1000`), not as immediate `0/N`.
- `05_random_rollouts` uses the notebook `ROLLOUTS` budget (default 100). `06_action_language` always uses 100 rollouts and counts one unit per legal action checked in visited states; per-check score is still proportional, but summary weighting keeps it comparable to other quality checks.
- Manual evaluation notebooks use `ROLLOUTS = 100` by default. Coding agents should not run the full evaluation pipeline unless the user explicitly asks.
- Pair oneshot-vs-agentic comparison uses `PAIR_ROLLOUTS` (default 1000, same scale as OpenSpiel comparison) — many independent lockstep games, not a handful of sampled actions.
- Before pair comparison or OpenSpiel comparison, run LLM action-language align on the generated code so `action_to_name` / `name_to_action` use an unambiguous comparison language.
- Action-language align runs immediately before OpenSpiel compare or pair compare, not before the base checks.
