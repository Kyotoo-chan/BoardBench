# Rule coverage

| Rulebook section / named rule | Implementing symbol | Probe or rationale | Assumption |
|---|---|---|---|
| Spielidee; most coins wins | `returns`, `_finish` | terminal scoring probe | none |
| Spielmaterial & Spielvorbereitung; 104 cards, counts, 5 cards, 3/2 fields | `COUNTS`, `initial_state` | fixture self-check covers 3–5 players and inventory | seeded choice of starting player is evaluator representation |
| Hand order / no sorting | `initial_state`, `apply_action` | rollout and observation round-trip | none |
| Spielablauf; active player clockwise, four phases | `legal_actions`, `apply_action` | agentic rollout | none |
| Wichtige Regeln für den Bohnenanbau; one type per field, same type on several fields | `_fits`, `_plants` | source-only fixture/action probe | none |
| Phase 1; first mandatory, second optional, no third | `legal_actions`, `apply_action` | rollout | none |
| Die Bohnenernte / all eight beanometers | `METERS`, `_payout` | source-only threshold inspection | none |
| Bohnenschutzregel | `_harvests` | source-only singleton/multi-field probe | none |
| Phase 2 reveal two | `_draw_one`, `apply_action(reveal)` | rollout | none |
| Regeln für den Bohnenhandel; active player trades, consent, hand/revealed only, unequal counts, gifts | trade branches in `legal_actions` / `apply_action` | proposal accept/reject fixture round-trip | A-01 limits one canonical proposal bundle |
| Phase 3; all traded and remaining revealed cards planted | `_plants`, `plant_received` branches | multi-owner fixture | planting owner/order represented explicitly |
| Phase 4; draw three to hand back, clockwise next player | `apply_action(draw)` | rollout | none |
| Ein leerer Nachziehstapel | `_draw_one` | recycle fixture | none |
| Ende des Spiels; third depletion, finish phases 2/3, harvest fields, ignore hands, clockwise tiebreak | `_draw_one`, `_finish` | terminal fixture and source-only depletion probes | none |
| Start card remains with starting player | `start_player` | serialization round-trip | physical card represented as fixed player id |

The illustrations and examples introduce no additional named card or combination beyond the eight bean types and examples already covered above.
