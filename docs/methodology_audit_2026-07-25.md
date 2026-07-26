# Methodology audit and repetition plan — 2026-07-25

## Status

This note supersedes the causal classifications proposed in the untracked `MODEL_BLINDNESS_ENFORCE.md`. It does not alter frozen implementations, raw evaluations, scenario outcomes, or historical commits.

## Corrections to interpretation

1. **Scenario scores are scenario-level.** “Clear” and “human decision” values count passed evaluated scenarios in those basis groups. They do not measure complete rule-fact or material-claim coverage. “Coverage” means configured scenarios that reached an evaluated outcome.
2. **A detected implementation defect and an evaluator gap are different events.** A missing scenario does not cause generated code to be wrong; it can only leave that defect unmeasured by that evidence group.
3. **`n=1` does not establish a model-inherent cause.** Report observed translation behavior under the recorded model, prompt, source condition, and workflow. Causal labels such as “model-inherent blindness” are unsupported.
4. **Human decisions remain hidden in original conditions.** Failure against an evaluator-approved decision is evidence of a source gap or decision-sensitive deviation, not proof that the original-condition implementer ignored supplied requirements.
5. **Independent reviews are fallible qualitative signals.** A same-model Judge miss is observed disagreement; same-family causation requires a controlled cross-family comparison.

## Frozen-run dispositions

### Wizard (`4eac6a4` → `5c30316` → `042748f`)

- Keep the committed original implementation and evaluation unchanged.
- The Wizard-led suit-obligation defect is confirmed by source, code inspection, three neutral reviews, the rule-fidelity persona, and a post-hoc deterministic diagnostic. The diagnostic is not added to the frozen 21-case score.
- Describe `11/11` as **11/11 configured clear-basis scenarios**, not complete clear-rule coverage.
- `WIZ-R14` is a separate human-decision-basis failure after `Narr → Zauberer → ordinary card`; the controlling decision was not model-facing.
- A future rubric may split the combined `WIZ-WIN-02` fact into atomic winner and legality claims and add a Wizard-lead/off-suit scenario under a new rubric hash.
- Do not rerun Wizard solely to repair the evaluated implementation. If Wizard becomes an original-versus-clarified experiment, generate a fresh original and clarified pair under the same new frozen rubric.

### Abalone (`daf80dc` → `cffdba8` → `d75d7f7`)

- Keep the PDF-only run unchanged.
- Report forced pass as a visible `0/1` human-decision-basis result. It was not supplied to the implementer.
- Do not claim a reachable-game deadlock from `ABAL-R19`: its sparse nonterminal fixture is evaluator-constructed and reachability from the ordinary setup was not established.
- A clarified Abalone run would require a separate attributed clarification artifact and a fresh run ID; never retrofit the forced-pass decision into the original packet.

### Exploding Kittens (`f8f4616` original; `b5b9cc3` clarified)

- Retain both runs as historical pilot evidence.
- Their observed `18/22 → 22/22` difference is reproducible, but the intervention changed a publisher PDF into a combined clarified TXT containing publisher text plus 24 decisions. Source format and presentation are therefore confounded with clarification.
- Do not use this pair as a clean current-protocol causal estimate.
- If Exploding Kittens is used as central thesis evidence, repeat both conditions as specified below.

### CATAN (`ff54365` → `3508766` → `74d6f96`)

- Keep the committed `54/59` original-condition result unchanged as historical iteration v1, including its crash.
- Retain but exclude the contaminated first Judge set; the three replacement reviews are the reported Judge evidence.
- Treat CATAN as an observational complexity/stress case, not clarification-effect evidence.
- Promote qualitative privacy or query-mutation concerns to hard findings only after a deterministic cited scenario is frozen and replayed.
- CATAN is excluded from the planned v2 reruns because its complexity would dominate the iterative study. Mention it only as a bounded historical stress case; do not use it as fixed central evidence.

### Bohnanza Base 2023 (`a076a9b`, documentation `b624c4f`)

- Keep the fresh `34/41 → 39/41` pair and byte-identical-PDF-plus-separate-clarification design unchanged.
- Interpret the Garden payout and non-active phase-three recipient as distinct observed changes.
- Treat the three phase-four fail-to-pass cases jointly with terminal cleanup: the original already stopped immediately but then incorrectly cleared/scored the hand. Do not count those cases as three independent timing mechanisms repaired by clarification.
- Keep the two final-harvest failures and scenario/Judge disagreement prominent.
- Exponential trade enumeration is code-proven; “unusable” remains an unmeasured performance claim until a reachable fixture and threshold are frozen.
- The pair used procedural packet isolation but predates the enforced filesystem canary. State that limitation. Repeat only if every central main-study pair must share the new hard-isolation protocol; never overwrite this pair.

## Iterative study design

BoardBench may use several sequential, versioned attempts for one game. Each attempt is retained as development evidence rather than discarded in favour of the best score.

- Give every iteration a new run ID, methodology version, frozen rubric hash, and recorded reason for change.
- Evaluation findings may inform the next iteration, but code is never repaired after evaluation under the same run ID.
- A later iteration is an adapted successor, not an independent replicate. Report the trajectory and every intervention rather than treating attempts as exchangeable samples.
- Declare the final iteration before launching it; do not select the highest score post hoc.
- After development games stabilize the workflow, freeze it and apply it to at least one untouched confirmation game.

For each source, split rules into atomic claims and classify each claim as:

1. `clear` — directly supported by a stable source locator and quote;
2. `ambiguous` — multiple materially different readings remain plausible;
3. `missing` — required behaviour is not specified;
4. `conflicting` — assigned sources give incompatible requirements;
5. `untestable` — the claim cannot be deterministically observed through the public contract.

Every deterministic, material `clear` claim should have at least one hard scenario or an explicit coverage exception. Ambiguous, missing, and conflicting claims remain visible in the original condition but are not scored against an arbitrary hidden decision. User-approved resolutions enter only the separate clarification artifact and become hard expectations for the clarified condition. Report claim-to-scenario mapping coverage and evaluated-claim coverage separately from scenario pass rate; mapping is not proof that every clause was asserted.

Player-count support is a required hard-rule family whenever the source states a supported range. For every listed count, test constructor acceptance, source-correct setup quantities, a legal initial action, and bounded playability; test rejection outside the range and every count-specific setup difference. A mismatch between the stated range and available components is recorded as a source conflict rather than silently patched.

## Hardened protocol for every new main-study run

Before generation:

1. Commit and freeze the source register, hashes, rule facts, environment profile, scenario suite, adapter, prompts, and self-checks.
2. On Windows, configure the persistent sandbox once with `generation/setup_codex_isolation.py`, then run `generation/check_codex_isolation.py`; failure blocks generation. Never create a fresh `CODEX_HOME` per run.
3. Validate source roles and hashes with `generation/source_condition.py`.
4. For a clarified condition, require byte-identical non-clarification sources plus exactly one separately attributed clarification artifact. Original packets reject clarification roles.
5. Construct the model packet outside every Git worktree and compare its recursive file list with an exact allowlist immediately before launch.
6. Record every packet file/hash, permission profile, and successful isolation canary in the agentic artifact.
7. Keep evaluator facts, scenarios, adapters, prior implementations, reviews, and scores outside the model-visible workspace.
8. `generation/codex_native.py` refuses every agentic launch unless it receives and validates the source condition and exact packet allowlist. Historical frozen runners that do not implement this new call contract intentionally fail closed; do not retrofit and rerun them under an old run ID.

During and after generation:

1. Within each versioned iteration, use one fresh final implementation per source condition, the same model/thinking/prompt/profile, and the bounded evaluator-neutral repair policy.
2. Never repair after evaluation under the same run ID.
3. Report technical gate, robustness, interface, clear-basis scenarios, human-decision-basis scenarios, scenario evaluated coverage, and Judges separately.
4. Post-hoc scenarios receive a new rubric hash and diagnostic label; they never alter a frozen historical score.
5. With one implementation per condition, make no run-variance or model-inherent claims.

## Exploding Kittens clean repetition

### Sources

- **Original:** unchanged publisher PDF, SHA-256 `f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853`, plus all freshly rendered 150-DPI pages.
- **Clarified:** the byte-identical PDF and page images plus a new separately attributed JSON clarification artifact.
- Derive clarification candidates from the historical 24-item TXT appendix, but re-review every item against the PDF, classify its basis, and obtain explicit user approval. Do not copy the normalized publisher text into the clarification artifact.

### Freeze

- Use one new environment profile, prompt, contract, self-check set, and evaluator rubric identically for both conditions.
- Freeze exact packet manifests and hashes before either generation.
- Preserve R11, R12, R16, and R22, but review all 22 scenarios for atomic claims, exact check timing, and whether each expectation is genuinely clear or clarification-dependent.
- Record the source-format-confounded historical pair as pilot context only.

### Execution

1. Fresh original generation; no access to clarification or evaluator artifacts.
2. Fresh clarified generation; only the approved clarification JSON differs.
3. Evaluate both with the same frozen technical checks, scenarios, and Judge protocol.
4. Store under new run IDs such as `pdf_hardened_1` and `clarified_hardened_1`; do not replace `pdf/` or `clarified/`.
5. Interpret differences as one paired observation under controlled source packaging, still with `n=1` per condition.

## Compact iteration layout

Do not overwrite historical bytes or duplicate whole result trees. Existing game-specific result paths are iteration v1 and remain Git-addressable. New reruns use one flat `results/scores/<game>/v2/` directory with condition-prefixed canonical files (for example `original_result.json`, `clarified_result.json`, `original.py`, and `clarified.py`) plus one shared `raw/` directory for Judge events/usage. Copy the single active run idempotently with `generation/archive_iteration.py`; its manifest refuses changed bytes. The game README points to v2 as the current presentation while identifying the legacy v1 paths. Later iterations use `v3/`, not `final-final` folders. `outputs/` remains the single-active-run workspace and is copied into the iteration directory only once.

The planned v2 roll-up covers Wizard, Abalone, Exploding Kittens, and Bohnanza Base 2023. CATAN remains peripheral historical evidence only. For each game, first expand and freeze atomic claims/player-count cases, then generate a fresh original condition; create the clarified condition only from cited ambiguous, missing, or conflicting claims approved after the original review. Clear-rule implementation failures remain hard expectations in both conditions and must not be disguised as source gaps.

## Recommended study order

1. Finish and commit workflow hardening before any new generation.
2. Repeat Exploding Kittens if it remains central causal evidence.
3. Continue Dominion only after the matching publisher companion is supplied and verified; it can become a complexity replication under the hardened protocol.
4. Add a clarified condition only after original-run gaps are reviewed and approved as a separate intervention.
5. Rerun Bohnanza or Wizard only if protocol comparability is required for the final main-study set; otherwise retain them with the limitations above.
