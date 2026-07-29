# Rule coverage

All probes use only source-derived states/actions. `Game` methods named below are in `implementation.py`.

| Supplied section / named rule | Implementing symbol(s) | Probe or non-probe reason | Assumption |
|---|---|---|---|
| Spielidee | `Game._finish`, `returns` | Rollout and terminal fixture: most coins wins | none |
| Spielmaterial & Spielvorbereitung; 104 cards; 3–5 players; two fields; five hand cards | `COUNTS`, `Game.__init__`, `initial_state` | `profile_fixture_self_check.py` inventory/count fixtures | A-01 start-player method |
| Hand order may not change; front card visible | hand lists; `legal_actions`; `observation_to_data` | privacy fixture and phase-1 rollout | none |
| Four phases / clockwise active player | `legal_actions`, `apply_action` | agentic phase rollouts | none |
| Bean planting: one variety per field; same variety on several fields; cards overlap | `_can_plant`, field lists | legal-action rollout | none |
| Phase 1: first card mandatory; second card optional; empty hand skips | `plant_first`, `plant_second`, `pass` | agentic rollout | none |
| “Die Bohnenernte”: incompatible planting forces a harvest | absence of plant action until a legal `harvest` | legal-action rollout | none |
| Phase 2: reveal top two cards | `reveal`, `_draw_one` | agentic rollout and recycle fixture | none |
| Trade: active player alone trades; all hand cards; revealed cards; no onward trading; no field cards; unequal quantities | `_trade_proposals`, `trade_propose`, pending snapshot refs | action round trips and trade fixture | A-02 finite proposal bound |
| Trade agreement; cards remain in hand until agreement | `trade_accept`, pending snapshot refs | trade-response fixture | none |
| Traded cards placed beside fields, never taken into hand | `pending_received` | phase-3 fixture | none |
| Gifts require recipient consent | gift `trade_propose`, accept/reject | trade-response action probe | A-02 |
| Phase 3: all traded and revealed cards must be planted; player chooses order | `plant_received`, `_next_phase3_actor` | multi-owner fixture | A-03 because cross-player/order procedure is absent |
| Phase 4: draw three, preserve order behind hand; next player clockwise | `draw`, hand append, `apply_action` | agentic rollout | none |
| Harvest any time, including outside active turn | harvest actions at stable decisions | action rollout | contract defines stable decision boundary |
| Bean meters: Garten 2/3; Rot 2/3/4/5; Auge 2/4/5/6; Soja 2/4/6/7; Brech 3/5/6/7; Sau 3/5/7/8; Feuer 3/6/8/9; Blau 4/6/8/10 | `METERS`, harvest branch | source-only threshold probes are directly representable; not separately scripted | none |
| Harvest: flip paid cards to coin pile, discard remainder, field empty | harvest branch; `coins`; `discard` | coin inventory fixture and rollout | none |
| Bean-protection rule | `_harvestable` | legal-action source fixture is representable; rollout exercises it | none |
| Empty deck: shuffle discard; game ends after deck empties third time | `_recycle_or_end`, `_draw_one` | recycle fixture and rollout | none |
| End during phase 2: finish phases 2 and 3 (even with one revealed card); no phase 4 | `_draw_one`, reveal/end-trade branches | depletion transition is exercised by rollout; fixture reconstruction covers depleted deck states | none |
| End scoring; hand ignored; each coin card worth one; clockwise-furthest tied player wins | `_finish`, `returns` | terminal fixture | none |
