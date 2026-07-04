# BoardBench one-shot generation packet
- game: mahjong
- variant: oneshot
- backend: claude
- expected code path: outputs/mahjong_oneshot.py
- expected response path: outputs/mahjong_oneshot.md

## Instructions for Claude
Use only the listed attachments and rulebook material.
Do not read BoardBench checks/.
Return assumptions plus one fenced ```python block with the full module.

## Attachments
- D:/safen/Ben_T/Studium/8.Semester/BoardBench/prompts/rulebook_to_python.txt
- D:/safen/Ben_T/Studium/8.Semester/BoardBench/prompts/open_spiel_backbone.md
- rulebook: inputs/game_rules.pdf (active copy of D:/safen/Ben_T/Studium/8.Semester/BoardBench/inputs/games/mahjong/game_rules.pdf)

## Notebook
- Run from evaluation2.ipynb with GAME set to this slug.
- After Claude responds, save to outputs/<game>_oneshot.md and run ingest_generation_response().