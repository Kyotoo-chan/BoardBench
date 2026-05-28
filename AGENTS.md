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
- one comparison notebook
- one append-only question/problem tracker

Avoid introducing large frameworks, provider abstractions, or complex evaluation pipelines unless explicitly requested.

## Hard rules

1. Keep the repository minimal unless the user asks for more structure.
2. Do not silently introduce API-key based workflows when the current task is subscription-first/manual.
3. Do not assume external game knowledge if the task says to rely only on the provided rulebook/text.
4. Keep raw model outputs whenever the workflow touches model generations.
5. Do not delete, reorder, or clean up entries in `QUESTIONS.txt` automatically.
6. Prefer readable files and explicit documentation over hidden magic.
7. Call out deviations from the agreed plan explicitly.

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

## Questions and problems

If a task reveals ambiguity, uncertainty, or a research decision that should be discussed with the professor, record it in `QUESTIONS.txt` as a new appended bullet instead of silently resolving it in architecture.
