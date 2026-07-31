# 6 nimmt! Version 2.3 — V2 Original findings

- Condition: byte-identical publisher PDF plus separately attributed user component observation; no publisher companion or clarification artifact.
- Scope: base game for 2–10 players, full default match ending after a completed game when a cumulative score exceeds 66; professional and optional target/game-count variants excluded.
- Generation: `gpt-5.6-sol`, thinking `low`; three calls and two evaluator-neutral pre-evaluation contract repairs.
- Judges: three fresh neutral `gpt-5.6-sol`, thinking `medium`; persona reviews remain separate.
- Agentic gate: PASS.
- Technical gate: 4/4.
- Robustness: 100/100.
- Interface: 77,788/77,788.
- Player counts: 11/11 (2–10 accepted; 1 and 11 rejected).
- Clear-basis scenarios: 24/24.
- Human-decision-basis scenarios: 9/9.
- Scenario evaluated coverage: 33/33 groups and 74/74 named cases.
- Claim-to-scenario mapping: 30/30 required clear claims; evaluated-claim coverage 30/30. Mapping is not complete assertion coverage.
- Neutral Judges: 0.84 / 0.88 / 0.82; mean 0.847, sample SD 0.031.

The evidence groups are not combined into a correctness score.

## Scored scenario findings

None. Every configured R2 scenario reached an evaluated PASS. This finite suite does not establish exhaustive rule fidelity.

## Confirmed unscored defect

Two neutral Judges independently reported that an uninterrupted round can erase the mandatory joint reveal before all players can observe every identity. A deterministic post-judge replay confirms the defect:

- source fact: `6N-C-JOINT-REVEAL`;
- PDF page 1: “Erst dann, wenn der Letzte sich entschieden hat, werden die Karten aufgedeckt.”;
- fixture: row `[10,11,12,13]`, commitments 20/30/50/70;
- transition: card 20 becomes the fifth card, then card 30 captures that row during the same atomic resolution;
- actual: players 0, 2 and 3 never observe identity 20 because completed `revealed`/`resolved` data are cleared and player 1's captured identities are private.

This replay is stored in `raw/judge_candidate_replays.json`. It was proposed after the frozen R2 suite ran, so it is a confirmed future regression candidate and **does not retroactively alter 24/24 clear-basis scenarios**.

## Disputed and adjudication-dependent Judge findings

### Imported `match_target`

Judges 2 and 3 penalized `state_from_data()` for accepting a base-state `match_target` other than 66. The frozen representation profile declares `match_target` only as `int`, and the contract requires every complete profile-valid fixture—including unusual, unreachable fixtures—to reconstruct. The bounded pre-evaluation repair therefore intentionally removed undeclared semantic reachability restrictions. This is a profile/contract design gap, not a confirmed implementation contradiction under the frozen contract. The generated initial and reachable match path use 66 and pass strict 66/67 scenarios.

### Semantic deserialization invariants

Persona reviews proposed rejecting duplicate/out-of-range cards, unusual row counts, inconsistent pending states and cross-`Game` player configurations. Those proposals conflict with the frozen contract's representation-only fixture boundary unless the profile first declares such cross-field invariants. They remain evaluator-design candidates, not scored defects. Exact JSON-domain fields, declared scalar ranges and action actor/parameter ranges are enforced.

### Terminal rendering

Judges 2 and 3 note that terminal `render()` prints `total_bullheads+game_bullheads` after the final game subtotal has already entered the cumulative total. Winner calculation and state scores are correct; the text can nevertheless suggest double counting. This is retained as a minor presentation risk.

### Own commitment identity

The executable-systems persona asks whether a player observation should retain the player's own committed card identity for perfect recall. The approved observation profile exposes commitment status but not that identity. This is a human-decision/profile question, not a publisher-clear defect.

## Material assumptions

The generated artifact declares four material assumptions:

1. private irreversible seat-ordered commitments;
2. shared minimum-score winners and +1/−1 terminal returns;
3. omitted `num_players` selects two players;
4. omitted `seed` selects deterministic seed zero.

The approved fact inventory additionally resolves component identities, complete bullhead inventory, seeded lifecycle, invalid-count rejection, observation redaction and pending low-card resolution. The model's declaration count is not a count of all approved source gaps.

## Evaluator history

The generated implementation was never changed after evaluation began.

1. Frozen R1 replay: 14 PASS / 19 CRASH because the shared runner constructed the generated module's valid default two-player `Game` while four-player fixtures were supplied. Invalid and unscored.
2. First compatibility replay: 32 PASS / 1 FAIL because joint visibility was tied to the transient `revealed` list rather than any canonical public location. Invalid and unscored.
3. R2: explicitly constructs the shared fixture game with four players and checks visibility across public rows, revealed records and resolved records. An outcome-blind reviewer confirmed that IDs, facts, bases, titles, source evidence, expectations and all 74 case names remained unchanged.

Both invalid replay JSON files and the R2 revision manifest are retained under `raw/` and `inputs/games/6_nimmt/evaluator_revision_v2_r2.json`.
