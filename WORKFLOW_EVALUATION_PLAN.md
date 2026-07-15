# BoardBench workflow and six-variant experiment

**Decision date:** 2026-07-14

**Game:** Exploding Kittens NSFW Edition

**Canonical rulebook:** `inputs/game_rules.pdf`

**Canonical SHA-256:** `f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853`

## Goal

BoardBench tests how reliably an LLM can translate a fixed board-game rulebook into an executable Python environment and which evaluation layers are needed to distinguish:

1. unclear, incomplete, or contradictory source rules;
2. implementation errors made by the model;
3. false or missed findings made by the evaluator.

A failed implementation is not by itself evidence that the rulebook is bad. A high technical or judge score is not by itself evidence of rule fidelity.

## Execution model

Pi orchestrates the experiment. Every implementation and judge call runs natively and ephemerally through Codex CLI with:

```text
model: gpt-5.6-sol
reasoning effort: medium
```

Implementation calls run in isolated temporary workspaces. To keep the generation condition native and comparable, the implementer receives only its assigned rulebook variant, the minimal public API contract, and an evaluator-neutral self-check. Canonical and variant-specific evaluation facts remain hidden. It cannot access repository checks, canonical scenarios, other variants, previous implementations, or reviews.

A provider mode named `agentic` is not sufficient evidence. The implementation agent must create `implementation.py`, map every supplied section and named rule/card/combination to code and source-only probes in `rule_coverage.md`, run `python -m py_compile implementation.py` and `python agentic_self_check.py`, and pass the same independently repeated gate. Technical failures may trigger at most two blind repair calls in the same isolated workspace. Commands, repair calls, outputs, coverage audit, and final gate status are retained.

The original six-variant pilot predates this evidence gate. Its calls used agentic-capable Codex infrastructure, but individual runs may have behaved like one-shot generation; they remain historical pilot evidence and are not silently relabelled or replaced.

Judge calls are fresh, read-only, and mutually blind. They receive the canonical rulebook, approved canonical facts, and exactly one implementation. They do not receive deterministic check logs, other reviews, other variants, or prior scores.

## Runs

The original PDF is run first. Five derived conditions follow:

| Stem | Implementer input | Purpose |
|---|---|---|
| `expl_pdf` | unchanged original PDF | canonical baseline |
| `expl_txt` | faithful text extraction | PDF-versus-text input comparison |
| `expl_anon` | anonymized form of the faithful text | proxy for title/name familiarity |
| `expl_omit` | text with predeclared material omissions | whether evaluation detects missing source information and resulting behaviour |
| `expl_error` | text with predeclared plausible false rules or contradictions | whether implementation follows bad input and canonical evaluation catches it |
| `expl_vague` | text rewritten with deliberately vague and ambiguous material rules | whether ambiguity causes divergent assumptions or explicit uncertainty |

The exact transformations are recorded before inspecting generated implementations. Derived variants never overwrite the canonical rulebook.

## Evaluation reference

All six implementations are evaluated against the same frozen canonical rule facts and cited scenarios derived from the unchanged original PDF. This allows omissions, errors, and vague formulations to be detected as deviations from the canonical rules rather than accepted as their own ground truth.

Variant-specific rule analysis is retained separately to show what an agent could infer from the input it actually received. Material ambiguities in the canonical source require human approval before hard scenarios are frozen.

## Evidence groups

Results remain separate:

1. **Technical gate:** checks 01–04.
2. **Runtime robustness:** check 05.
3. **Interface/action language:** check 06.
4. **Rule fidelity:** canonical, page-cited public-API scenarios.
5. **Independent review:** three fresh `gpt-5.6-sol:medium` Codex judges per implementation.
6. **Uncertainty:** ambiguous, unsupported, or untestable rules and judge disagreements.
7. **Efficiency:** elapsed time, token usage, quota observations, and manual effort.

There is no primary aggregate correctness score across unlike evidence groups. Judge means and spread are reported as model signals, not ground truth. OpenSpiel and one-shot comparisons are excluded: every generation in this experiment is agentic and the game has no matching OpenSpiel oracle.

## Judge policy

Three same-model judges provide a majority signal and estimate within-model variability without introducing a cross-model condition. For every `critical` or `major` finding, a review must include:

- page/section and direct canonical rule quote;
- conflicting code symbol or transition;
- expected canonical behaviour;
- actual implemented behaviour.

Agreement, disagreement, confidence, uncovered rule areas, and requested regression scenarios are preserved. Repeated supported findings should later become deterministic tests. Judges remain fallible and are validated separately with known mutations.

## Artifact names

All runs are agentic, so no redundant `_ag` or `_os` suffix is used:

```text
outputs/<stem>.md
outputs/<stem>.py
outputs/<stem>_checks.txt
outputs/<stem>_judge_1.md
outputs/<stem>_judge_2.md
outputs/<stem>_judge_3.md
outputs/<stem>_usage.json
```

Raw Codex JSONL events, prompts or prompt hashes, model settings, timestamps, command metadata, response text, code, reviews, and grouped results are retained. Each numbered experiment is committed as a complete artifact set. Before the next generation, `outputs/` is cleared so the working tree contains only the current experiment; earlier sets remain reproducible from their Git commits. Temporary workspaces and judge packets are deleted after collection.

## Usage and cost data

Codex is invoked with JSON event output when supported. Per call and per variant, BoardBench retains as much provider-reported data as available:

- input tokens;
- cached input tokens;
- output tokens;
- reasoning tokens, when exposed;
- total tokens;
- start/end timestamps and elapsed seconds;
- exit status and retry count;
- model and reasoning effort;
- observed 5-hour and 7-day quota state, when available.

ChatGPT subscription use may not expose a true monetary cost per call. In that case the experiment reports token and quota consumption. Any conversion using published API prices is clearly labelled **API-equivalent estimate**, not actual subscription cost.

Efficiency information is contextual metadata for the current study, not a rule-fidelity score. The raw data is intentionally broader than the initial thesis tables so later analysis can narrow it without reconstructing unavailable runs.

## Comparison logic

- PDF versus faithful TXT estimates input-modality effects.
- Faithful TXT versus anonymized TXT estimates a familiarity proxy.
- Faithful TXT versus omission, error, and vague variants isolates controlled source degradation.
- Repeated fresh judges estimate review variability, not model-family independence.
- A failure shared across repeated implementations despite a genuinely undecidable source may indicate source ambiguity.
- A failure against a clear cited rule indicates an implementation defect unless evaluator validation disproves it.
- A judge finding unsupported by canonical evidence remains a question or evaluator error.

## Reproducibility rules

- Preserve the original PDF and every derived input with SHA-256 hashes.
- Record transformations before viewing outputs.
- Freeze canonical scenarios before comparing implementations.
- Never expose evaluator scenarios or prior outputs to implementers.
- Never expose check logs or previous reviews to judges.
- Do not silently edit completed experimental artifacts after methodology changes.
- Use real execution and commit timestamps; do not backdate or fabricate chronology.

## Evaluator revision policy

Evaluator changes after inspecting results are labelled post-hoc and versioned instead of replacing historical evidence. A version manifest hashes the rulebook, approved facts, scenario suite, state adapter, runner, and judge prompt, and points to the unchanged implementation commits.

Scenario outcomes are `PASS`, `FAIL`, `CRASH`, `UNREACHED`, or `UNTESTABLE`. Fidelity is calculated only over evaluated cases (`PASS+FAIL+CRASH`) and evaluated coverage is reported separately. Clear printed-rule scenarios and approved human-decision scenarios remain separate evidence columns.

Rare material interactions use evaluator-only deterministic state adapters. An adapter may construct and observe state but cannot encode the expected rule result. Search or LLM-proposed traces remain exploratory until replayed, human-approved, and included in a later frozen evaluator version.

Every hard scenario records stable fact IDs, page, direct quote, basis (`clear` or `human_decision`), exact starting state or public trace, selected action, expected observable transition, and the temporal point after reactions or choices at which it is checked.
