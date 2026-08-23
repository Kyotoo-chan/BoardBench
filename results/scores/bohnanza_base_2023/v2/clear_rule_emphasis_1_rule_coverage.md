# Rule coverage

Source: supplied German rulebook, pages 1–2. Probes below are source-only checks
implemented in `agentic_self_check.py`, `profile_fixture_self_check.py`, or direct
state/action probes; the evaluator contract and profile supply representation only.

| Source section / named rule | Implementing symbol | Probe or reason not probed | Assumption |
|---|---|---|---|
| Spielidee | `Game.returns`, `_finish` | Terminal winner/returns probe | A-03 tie detail |
| Spielmaterial & Spielvorbereitung; 104 cards; 8 types; 3 fields for 3 players, 2 for 4–5; five ordered hand cards; start card | `COUNTS`, `BEANS`, `initial_state` | Fixture inventory and 3/4/5-player setup probes | A-01 dealing order |
| Hand order may never change; front card visible | hand list convention, plant actions use index 0; `observation_to_data` | Privacy fixture checks front only | None |
| Four phases and clockwise active player | `legal_actions`, `apply_action` | rollout phase-transition probes | None |
| Bean planting: same type per field; same type may occupy several fields; cards stacked | `_plant_fields`, plant transition | direct legal-field probes | None |
| Phase 1: first card mandatory, second optional; forced harvest if no field; skip if hand empty | `legal_actions`, plant/pass transitions | rollout plus fixture probes | None |
| Phase 2: reveal top two; revealed cards belong to active player and may be traded | reveal/trade actions | rollout probes | None |
| Trade: only active player trades; any hand position; revealed cards; unequal multi-card bundles; no field cards; no re-trading received cards; consent; gifts | `_refs`, `_nonempty_subsets`, trade proposal/response transitions | canonical multi-card proposal probes; atomic acceptance | A-02 negotiation serialization |
| Agreed cards placed beside fields, not into hand; continue trading until active player stops | `pending_received`, `end_trade` | fixture and rollout probes | None |
| Phase 3: all traded/gifted and remaining revealed cards must be planted; owner chooses order | `plant_received` legal actions | multi-owner fixture | None |
| Phase 4: active player draws three to back of hand; next player clockwise | draw transition | rollout probes | None |
| Harvest at any time, including inactive player | `_harvest_actions`, `_harvest` | harvest exposed at stable decision states | Contract representation choice defines stable boundary |
| Beanometer payouts: Garten 2→2, 3+→3 | `METERS["gartenbohne"]` | direct threshold probe | None |
| Beanometer payouts: Rot 3/6/7/8→1/2/3/4 | `METERS["rote_bohne"]` | direct threshold probe | None |
| Beanometer payouts: Augen 2/4/5/6→1/2/3/4 | `METERS["augenbohne"]` | direct threshold probe | None |
| Beanometer payouts: Soja 2/4/6/7→1/2/3/4 | `METERS["sojabohne"]` | direct threshold probe | None |
| Beanometer payouts: Brech 3/5/6/7→1/2/3/4 | `METERS["brechbohne"]` | direct threshold probe | None |
| Beanometer payouts: Sau 3/5/7/8→1/2/3/4 | `METERS["saubohne"]` | direct threshold probe | None |
| Beanometer payouts: Feuer 3/6/8/9→1/2/3/4 | `METERS["feuerbohne"]` | direct threshold probe | None |
| Beanometer payouts: Blau 4/6/8/10→1/2/3/4 | `METERS["blaue_bohne"]` | direct threshold probe | None |
| Harvest procedure: count, read top card meter, flip paid cards, discard remainder, field empty | `_payout`, `_harvest` | coin-inventory fixture and direct probe | None |
| Bean protection: no singleton harvest if any field has more than one card | `_harvestable` | direct legal-action probe | None |
| Empty deck: shuffle discard to form new deck | `_draw_one`, `_rng_shuffle` | recycle fixture | None |
| End: third depletion; if during phase 2 finish phases 2–3; final harvest; hand ignored | `_draw_one`, phase-3 pass, draw, `_finish` | depletion fixtures/direct probes | None |
| Tie: tied player furthest clockwise from start wins | `_finish` | direct tied terminal probe | A-03 |
| Terminal states have no actions | `legal_actions` | agentic self-check | None |
| Canonical state/action/observation and private hands | serialization methods | both supplied self-checks | Representation only; no rule assumption |
