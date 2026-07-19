# Rule coverage — assigned 4–5-player base condition

Only the publisher rulebook pages 3–11 were used as gameplay evidence. Variant-only beans on pages 3 and 10–11 are audited below but excluded from this assigned base condition.

| Source section / named rule | Implementing symbol | Source-only probe / disposition | Assumption |
|---|---|---|---|
| Spielmaterial & Spielvorbereitung (p.3): 104 cards, 8 base beans; three fields for 4–5; start-player card; five ordered hand cards | `BEANS`, `COUNTS`, `Game.initial_state` | Counts sum to 104; initial states have 5 cards and 3 fields; front is index 0 | A-02 for randomization |
| Hand order, no sorting (p.4) | `plant_first`/`plant_second`, hand index 0 | Legal hand planting always uses index 0; trades remove indexed cards without reordering | none |
| Draw and discard piles (p.4) | `_draw_one`, `_reshuffle_or_end` | Deck is hidden; discard recycles on exhaustion | A-02 |
| Turn order and four phases (p.5) | `phase`, `apply_action` | State transitions plant → reveal/trade → plant received → draw → clockwise next active player | none |
| Bean-field construction: one sort per field; same sort may occupy several fields; cards overlap (p.5) | `_plant_actions`, `plant` | Plant only on empty or matching fields; duplicate-sort fields remain legal | none |
| Phase 1: mandatory first card, optional second; no third (pp.5–6) | `legal_actions`, `plant`, `pass` | First phase has no pass when hand nonempty; second has pass; then reveal | none |
| Empty hand skips to phase 2 (p.6) | `pass` in planting phases | Empty hand exposes pass | none |
| Phase 2: reveal exactly two, cards belong to active player, trade or plant (p.6) | `reveal`, `zones.revealed`, `trade`, `end_trade` | Reveal draws twice; leftovers move to active planting obligations | none |
| Trade restrictions (p.6): only active trades with others; others not among themselves; any hand position; active may trade revealed; received cards not retraded; field cards not traded; unequal counts allowed | trade action family and `pending` | Partner excludes active; offers use active hand/revealed; requests use partner hand; received zone has no trade actions; proposal sides can have unequal lengths | A-01 |
| Binding trade only after agreement; gifts require consent (p.7) | `trade_submit`, `trade_accept`, `trade_reject` | No cards move before accept; zero-sided proposals represent consensual gifts | A-01; profile gift vocabulary is not needed separately |
| Phase 3: all traded/revealed cards must be planted; player chooses order (p.8) | `plant_received`, `pending_received`, `_advance_received` | Each owner plants all obligations before draw; cards cannot enter hand | A-03 for inter-player sequencing |
| Phase 4: active draws three in order to back of hand; next clockwise player (p.8) | `draw` | Three sequential draws append to hand, then active increments modulo players | none |
| Die Bohnenernte: harvest at any time, including another player's turn; bean meter; empty field after harvest (pp.8–9) | `harvest`, `_coins`, `_harvest_actions` | Legal actions include every player's own harvest interrupts; coins reserved and remainder discarded; field cleared | none |
| Bean protection: singleton harvest only if no field has 2+ cards (p.9) | `_harvest_actions` | Singleton actions suppressed whenever any own field is multi-card | none |
| Empty draw pile: discard becomes new face-down pile (p.10) | `_reshuffle_or_end` | Depletion counter increments and discard is recycled | A-02 |
| End: third draw-pile exhaustion; finish phases 2 and 3 if exhaustion occurs during reveal; hands ignored; most coins; clockwise-farthest from start player breaks tie (p.10) | `_draw_one`, `returns` | Terminal has no actions; score uses coins only and stated tie-break | none |
| Blaue Bohne (20), Feuerbohne (18), Saubohne (16), Brechbohne (14), Sojabohne (12), Augenbohne (10), Rote Bohne (8), Gartenbohne (6), printed Bohnometers | `COUNTS`, `METERS`, `_coins` | Each named base bean has count and four-tier meter (unavailable Gartenbohne tiers are `None`) | none |
| Variante 1: Kakaobohne, Weinbrandbohne, Kaffeebohne; changed draw/end rules (p.11 heading referenced on p.3) | not implemented: outside assigned 4–5-player base condition | Audited and excluded | none |
| Variante 2 / Ackerbohne and its special harvest rule (pp.11–12 shown as pages 10–11) | not implemented: explicitly a variant for 4–5 players, not the assigned base condition | Audited and excluded | none |

The profile’s `reorder_hand` action is intentionally never legal because the source expressly forbids changing hand order. `third_field` is always true because the assigned 4–5-player setup starts with three fields.
