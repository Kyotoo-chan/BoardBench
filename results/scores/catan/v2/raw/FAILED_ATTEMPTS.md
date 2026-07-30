# CATAN V2 invalid attempts

## Original first evaluator replay — 2026-07-29

- The blind `v2_original_1` implementation passed its one-call pre-evaluation gate, technical checks, 100/100 rollouts, interface and player-count probes.
- The first scenario replay exposed evaluator/profile representation errors before Judges were launched:
  1. the gift case attempted an action it simultaneously expected to be illegal;
  2. development-deck list orientation was not declared, so a hard expected draw order was invalid;
  3. inherited historical expectations removed played/revealed development cards from the hand, while profile v2 represents every development card in `development_hand` with a `revealed` flag and records only played Knight/progress cards in `played_development`.
- The invalid 40 PASS / 11 FAIL replay is retained in `invalid_evaluator_replay_1.tar.gz`; it is unscored and unjudged.
- Corrections are evaluator-neutral representation fixes. The generated implementation is unchanged and will be replayed under a versioned rubric hash. Longest Road and progress-card-zone failures remain eligible implementation findings rather than being repaired away.

## Neutral-Judge packet r1 — discovered 2026-07-30

- The Original and clear-rule-emphasis r1 Judge packets copied the assigned publisher Almanac PDF but rendered only the primary rulebook.
- This violates the BoardBench requirement that every model-facing PDF be accompanied by freshly rendered images of every page at 150 DPI.
- All six reviews and their original result cards remain retained as method-invalid historical attempts; their scores are not used in the final comparison.
- `inputs/games/catan/judge_packet_revision_v2_r2.json` froze the correction before reruns. Packet r2 renders both PDFs completely, attributes the optional intervention separately, and reruns all three conditions without changing generated code or scenario results.
- Valid r2 raw events and usage are retained in `judge_packet_r2_raw.tar.gz`.
