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
