# 6 nimmt! Version 2.3 details

## Source condition

- `6NIMMT-V23-RULES`: AMIGO Version 2.3 publisher PDF, SHA-256 `b200ae0558c283ba86f331037402d9150675958ac6a6dc3e5df188435626539d`.
- `6NIMMT-V2-COMPONENTS`: user observation of card identities and complete bullhead inventory, SHA-256 `01e8f5dbe0cdca5ea514e628da3e5ed71ceb17729bbd22ac3a309c44cb2da950`.
- Component evidence supports only human-decision scenarios; no clear-basis scenario depends on it.
- Professional and optional target/game-count variants are outside scope.

## Workflow

The 42-claim inventory contains 32 clear, nine missing and one ambiguous claim. Thirty publisher-clear material testable claims required hard scenarios and achieved 30/30 mapping. The approved matrix contains 33 groups and 74 named cases: 24 clear-basis and nine human-decision-basis groups.

The blind implementation used `gpt-5.6-sol:low`. Two bounded evaluator-neutral repairs addressed the public contract before evaluation; all three generation calls, feedback and events remain under the single run ID. Evaluation then used the unchanged final implementation.

## Evaluator revision

The predeclared R1 runner implicitly reused `Game()` for all fixtures. The evaluator-only reference had defaulted to four players, while the generated implementation validly defaulted to two. This caused 19 fixture crashes unrelated to rules. A compatibility replay then exposed one representation-specific visibility assertion. Both invalid replays remain unscored.

R2 explicitly supplies `num_players=4` to the shared fixture game and treats a played identity as visible in any canonical public observation location. The revision was reviewed outcome-blind and preserves all approved scenario metadata and case names. See `inputs/games/6_nimmt/evaluator_revision_v2_r2.json`.

## Interpretation

The final configured suite passes 33/33, but this is finite scenario evidence rather than complete correctness. Neutral Judges found a joint-reveal information issue not exercised by the frozen fixtures. The proposed trace was replayed deterministically and confirmed, but remains unscored because it was added after evaluation.

Judge concerns about semantic deserialization restrictions conflict with the frozen representation-only contract and are reported separately as evaluator/profile design questions. No post-evaluation implementation repair was made.
