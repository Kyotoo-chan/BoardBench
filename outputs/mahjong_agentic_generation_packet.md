# BoardBench agentic generation packet
- game: mahjong
- variant: agentic
- backend: claude
- workspace: D:/safen/Ben_T/Studium/8.Semester/BoardBench/generation_workspaces/mahjong_agentic
- expected workspace code path: D:/safen/Ben_T/Studium/8.Semester/BoardBench/generation_workspaces/mahjong_agentic/outputs/mahjong_agentic.py
- expected repo response path: outputs/mahjong_agentic.md
- expected repo code path after ingest: outputs/mahjong_agentic.py

## Instructions for Claude / Cursor
Work only inside the workspace inputs/ and outputs/ directories.
Do not read BoardBench checks/ or other repo evaluation files.
You may run small syntax/import smoke checks on your own generated file.
Return assumptions plus one fenced ```python block with the final module.

## Workspace attachments
- D:/safen/Ben_T/Studium/8.Semester/BoardBench/generation_workspaces/mahjong_agentic/inputs/rulebook_to_python.txt
- D:/safen/Ben_T/Studium/8.Semester/BoardBench/generation_workspaces/mahjong_agentic/inputs/open_spiel_backbone.md
- D:/safen/Ben_T/Studium/8.Semester/BoardBench/generation_workspaces/mahjong_agentic/inputs/game_rules.pdf

## Notebook
- Run from evaluation.ipynb with GAME set to this slug.
- After Claude responds, save to outputs/<game>_agentic.md and run ingest_generation_response().