# Rule coverage — Variant 2: Die Ackerbohnen (4–5 Spieler)

| Source section / named rule or bean | Implementation symbol | Probe / disposition | Assumption |
|---|---|---|---|
| Spielmaterial & Spielvorbereitung (base game) | `Game.initial_state`, `COUNTS` | seeded deck; five ordered cards; two fields at 4–5 | none |
| Hand order / no sorting | `plant` legality, hand front index 0; draw appends | action/state round-trip and rollout | none |
| Spielablauf / clockwise active player / four phases | `apply_action`, `PHASES` | rollout transitions | none |
| Phase 1: mandatory first, optional second, never third | `legal_actions`, `apply_action` | legal-action phase probes via self-check | none |
| Bean planting: one sort per field; same sort on multiple fields | `_can_plant` | source-only legality logic | none |
| Forced harvest before incompatible planting | harvest actions remain available until a planting field exists | rollout/legal-action probe | none |
| Phase 2: reveal top two | `_draw_one`, `reveal` | seeded rollout | A-02 |
| Trading: active player only; any hand position; active may trade revealed; fields/received cards excluded; unequal counts permitted | `trade_start`, `trade_response`, `pending_received` | one-card atomic protocol; repeated trades | A-03 |
| Mutual consent and delayed removal | proposal then accept/reject | response-state probe | none |
| Gifts require recipient consent | `gift_propose`, `gift_accept`, `gift_reject` | response-state probe | none |
| Received cards stay off hand and cannot be retraded | `zones.pending_received` | observation/state probe | none |
| Phase 3: all received and untraded revealed cards mandatory; free order | `plant_received`, `_advance_planter` | rollout | none |
| Phase 4 (Variant 1 rule used by Variant 2): each player one card, active first clockwise | `draw` | rollout | A-01 |
| Harvest any time, including non-active player | `_harvestable`, harvest actions | Engine exposes harvest to the current decision player; response interruption is not allowed | none |
| Bohnometer, coins, discard, field becomes empty | `METERS`, `_do_harvest` | source-only threshold table | none |
| Bohnenschutzregel | `_harvestable` | singleton/multi-field legality | none |
| Empty deck: shuffle discard | `_draw_one` | deterministic seeded shuffle | none |
| Spielende: third empty deck for 4+; reveal exception; final harvest; hands ignored; coin count | `_draw_one`, `_finish`, `returns` | rollout plus terminal serialization | A-02 |
| Tie: clockwise farthest from start player | `returns` | direct source-only ordering logic | none |
| Variant 2 materials: eight base sorts + Weinbrand + Acker; two fields | `BEANS`, `COUNTS`, `initial_state` | deck composition probe | none |
| Ackerbohne: two grants third field, cards discarded; no reward if already third; three pays 3 | `_do_harvest` | source-only branch probe | none |
| Blaue Bohne (20; 4/6/8/10 → 1/2/3/4) | `COUNTS`, `METERS` | table audit | none |
| Feuerbohne (18; 3/6/8/9 → 1/2/3/4) | `COUNTS`, `METERS` | table audit | none |
| Saubohne (16; 3/5/7/8 → 1/2/3/4) | `COUNTS`, `METERS` | page 9 example + component audit | none |
| Brechbohne (14; 3/5/6/7 → 1/2/3/4) | `COUNTS`, `METERS` | table audit | none |
| Sojabohne (12; 2/4/6/7 → 1/2/3/4) | `COUNTS`, `METERS` | table audit | none |
| Augenbohne (10; 2/4/5/6 → 1/2/3/4) | `COUNTS`, `METERS` | table audit | none |
| Rote Bohne (8; 2/3/4/5 → 1/2/3/4) | `COUNTS`, `METERS` | table audit | none |
| Gartenbohne (6; 2→2, 3→3) | `COUNTS`, `METERS` | table audit | none |
| Weinbrandbohne (22; 4/7/9/11 → 1/2/3/4) | `COUNTS`, `METERS` | component observation; explicitly selected by Variant 2 | none |
| Kaffeebohne, Kakaobohne | excluded from `BEANS` | named in component source but Variant 2 explicitly selects Weinbrand, not these | none |
| Elsterbohne | excluded | rulebook says variant-only; no supplied component identity/value and Variant 2 does not select it | none |
| Startspielerkarte and overview cards | `start_player` / no mechanical overview object | start player retained for tie-break; aids omitted | none |
| Canonical state/action/observation | serialization methods | `agentic_self_check.py` | evaluator representation only |
