# Bohnanza Base 2023 clarified comparison preflight

Status: **PASSED — one clarified generation may start**

## Intervention

The clarified condition contains exactly two assigned rule sources:

1. the byte-identical publisher PDF used by the original run;
2. `clarifications.json`, a user-approved `experimenter_clarification` source covering only third-depletion timing, all-player phase-three planting/order, uncapped finite trade bundles, and a textual transcription of all eight beanometers.

The clarification is not presented as publisher text. The implementer receives no rulefacts, scenarios, adapter, previous implementation, scores, or reviews.

## Controlled comparison

The original and clarified generations use the same:

- model `gpt-5.6-sol`;
- low generation thinking and low verbosity;
- implementation prompt;
- Contract-v2 environment contract/profile;
- reachable-state and complete-fixture gates;
- technical, robustness, interface, scenario runner, and Judge prompt;
- one generation and one medium-thinking neutral Judge.

Only the approved clarification source differs.

## Frozen evaluator

The comparison rubric contains 37 deterministic scenarios. It adds exact-card depletion boundaries, non-active phase-three progression and order choice, legal 1-for-2 and 3-for-1 trades, and the textual Garden payout evidence. It was frozen before the clarified generation and is applied identically to both implementations.

Original implementation baseline under this rubric:

- PASS 31
- FAIL 6
- CRASH 0
- UNREACHED 0
- UNTESTABLE 0

## Zero-token checks

- Manifest and all source/infrastructure hashes match.
- Packet-content regression confirms the exact full task prompt and both assigned sources.
- Full 14-method API probe passes.
- Complete profile-fixture probe passes.
- All 37 comparison fixtures execute with zero crash/untestable outcomes through the infrastructure probe.
- 36 focused regression tests pass.
- No clarified progress file, accepted run, Judge, or `outputs/` artifact exists.
- At most two evaluator-neutral repair calls are permitted; persistent gate failure stops before judging.
