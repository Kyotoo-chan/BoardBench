---
name: bbimpl
description: Generate one isolated game implementation.
---

# BoardBench implementation

Example:

```text
/bbimpl game=conect subagents=on submodel=openai-codex/gpt-5.6-sol subthinking=low
```

Use the argument and subagent policy from `/bb`.

## Preconditions

Require the archived assigned source condition (primary rulebook, optional verified publisher companion, and optional component appendix), `inputs/games/<slug>/rulefacts.md` with `status: approved`, and `checks/scenarios/<slug>.json`. Return to `bbedge` for material unresolved rules or source conflicts.

## Implementation

1. Run `python generation/clean_outputs.py`, then `python generation/clean_outputs.py --check-empty`. The cleaner must refuse to delete uncommitted artifacts; commit the prior active run first. Do not begin generation unless `outputs/` is empty apart from `.gitkeep`.
2. Read `inputs/prompts/rulebook_to_python.txt`.
3. Create an isolated temporary workspace containing every document in the assigned source condition, freshly rendered 150-DPI images of every page of every assigned PDF from `generation/pdf_pages.py`, their render manifests, a short source manifest identifying each publisher/user role and hash, `inputs/prompts/environment_contract.md`, the frozen `inputs/games/<slug>/environment_profile.json`, the prompt, `generation/agentic_self_check.py`, and the game-local `inputs/games/<slug>/profile_fixture_self_check.py` when present (otherwise the generic `generation/profile_fixture_self_check.py`). Give the implementer both each original PDF and all its page images. State the approved base/variant scope explicitly in the source manifest and task instead of cropping the PDF; require out-of-scope sections to be acknowledged but not implemented. A clarified condition adds its separately attributed approved clarification artifact to the unchanged PDF packet; extracted text never replaces a PDF. Contract/profile files define representation only and are not game-rule sources. Approved evaluator facts, repository checks, and scenario expectations remain hidden from the implementer.
4. Native Codex implementation generation defaults to `gpt-5.6-sol:low`. If Pi subagents are enabled, launch one `implementer` Agent as the only writer. Pass explicit child model/thinking exactly. Otherwise omit those fields so it inherits, or choose only a demonstrably weaker setting than the parent.
5. Require the Agent to create `implementation.py`, implement the five canonical state/action/observation data methods from the contract/profile, audit every supplied rulebook section/named rule into `rule_coverage.md`, and run `python -m py_compile implementation.py`, `python agentic_self_check.py`, and `python profile_fixture_self_check.py` against the actual file. New main-study runs use the versioned protocol that also requires schema-valid `assumptions.json` containing only material source assumptions, their alternatives, selected behavior, and affected mechanics. A model setting named `agentic` is not evidence by itself.
6. Independently rerun both self-checks and validate required audit artifacts without comparing them to hidden evaluator expectations. A crash, technical/API/self-check failure, or objectively source-required omission found by this pre-evaluation audit returns only evaluator-neutral feedback to the same isolated implementation workflow for at most two repair rounds. Never reveal cited scenarios. If no attempt passes, record the run as failed and do not evaluate its implementation.
7. Preserve the canonical artifacts listed in `AGENTS.md`. Consolidate model/usage, source/render manifests, repairs, gate status, and artifact hashes into `<stem>_agentic.json`; do not emit duplicate response, agent-input, agent-output, meta, status, log, or standalone manifest files. Repair attempts belong to one generation run and are not scored separately; copy only the final gate-passing implementation.
8. Remove the workspace.

## Checks

Run through the `boardbench` Conda environment and keep groups separate:

1. technical 01–04;
2. robustness 05;
3. interface 06;
4. rulebook scenarios.

Do not combine them into a correctness score. Only technical/API/self-check defects may enter the blind repair loop. Changed rule interpretations return to the user. Do not call a run agentic unless the actual implementation file was written, tested, and passed the independent gate.

End with paths, grouped results, parent and child model/thinking, assumptions, and the next `/bbeval` command.
