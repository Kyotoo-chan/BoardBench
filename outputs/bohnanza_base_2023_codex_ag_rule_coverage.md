# Rule coverage

The only behavioral source is the supplied two-page German rulebook. Contract/profile references below concern representation only.

| Source section or named rule | Implementing symbol | Source-only probe / status | Assumption |
|---|---|---|---|
| Spielidee | `Game._harvest`, `Game._finish`, `Game.returns` | Full rollouts score coins and select a winner | — |
| Spielmaterial & Spielvorbereitung; 3 players use 3 fields, 4–5 use 2; 104 cards; five hand cards | `COUNTS`, `Game.initial_state` | `profile_fixture_self_check.py` inventory and all supported counts | — |
| Card counts: Garten 6, Rot 8, Auge 10, Soja 12, Brech 14, Sau 16, Feuer 18, Blau 20 | `COUNTS` | Initial inventory counter fixture | — |
| Hand order may never change; front card is visible | `_plant_actions`, `_plant`, `observation_to_data` | Privacy fixture and rollout action generation | — |
| Setup draw/discard/coin stacks | `Game.initial_state`, `GameState.zones` | Initial-state canonical round trip | — |
| Start player and clockwise turns; start card not passed | `initial_state`, `apply_action` (`draw`) | Seed reproducibility and rollouts | Profile represents the start card as `start_player` |
| Four phases | `PHASES`, `legal_actions`, `apply_action` | Rollout traverses all stable phases | — |
| Field contains only one bean type; same type may occupy multiple fields; cards overlap | `_plant_actions`, `_validate_state`, `_plant` | Fixture validation and legal plant probes | — |
| Phase 1: mandatory front card, optional second front card; harvest first if needed; empty hand skips | `_plant_actions`, `legal_actions`, `_plant`, `pass` | Rollouts and fixture-derived phase probes | — |
| Phase 2: reveal top two deck cards; active player owns them; negotiate | `_draw_one`, `reveal`, `_trade_actions` | Seeded rollout | — |
| Trading: active player trades with all; others not with each other; hand position irrelevant; revealed allowed; acquired/field cards may not be retraded; unequal quantities allowed | `_trade_actions`, `_accept`, `pending_received` | Trade-response fixture plus rollout proposals | A-02 (atomic proposal granularity) |
| A deal requires both players' consent; do not remove cards before acceptance | `trade_propose`, `trade_accept`, `trade_reject`, `_accept` | Trade fixture confirms snapshot refs and both responses | — |
| Gifts require consent; rejection cancels | gift form of `trade_propose`, response actions | Rollout legal-action acceptance | A-02 |
| Received cards lie beside fields and may not enter hand | `zones.pending_received`, `_accept` | Trade fixture and phase-3 fixture | — |
| Phase 3: plant all traded and remaining revealed cards; owner chooses order | `plant_received`, `_plant_actions`, `_plant` | Multi-owner phase-3 fixture | — |
| If no matching field, harvest before planting | harvest actions coexist with phase-3 planting | Rollout legal-action application | — |
| Phase 4: draw three cards in order behind the hand; next player clockwise | `draw`, `_draw_one`, `apply_action` | Seeded rollouts | — |
| Harvest at any time, even when inactive | `_harvest_actions` in every stable nonterminal state | Rollout checks every offered action | Contract’s stable-decision boundary |
| Beanometers and zero-coin harvests | `METERS`, `_harvest` | Sojabohne example (2→1, 3/4→2, 5/6→3, 7+→4); other printed cards visually mapped | — |
| Harvest procedure: count, consult top card, flip paid cards, discard rest, field becomes empty | `_harvest` | Inventory-preserving fixture/rollout transitions | — |
| Bohnenschutzregel: no singleton harvest while another own field has multiple cards | `_harvest_actions` | Source-derived constructed-state logic | — |
| Empty deck: shuffle discard as new deck | `_draw_one` | Recycle fixture and seeded transition | — |
| End: deck empties third time; phase-2 occurrence finishes phases 2 and 3; harvest all fields; hand ignored | `_draw_one`, `apply_action`, `_finish` | Terminal fixture and rollouts | A-01 for phase-4 exhaustion |
| Tiebreak: tied player farthest clockwise from start player | `_finish` | Source-derived order calculation | — |
| Terminal states expose no actions | `legal_actions` | Both self-checks | — |
| Canonical state/action/observation, private hands, chance counter, reserve | serialization methods | `agentic_self_check.py`, `profile_fixture_self_check.py` | Representation only, not a rule assumption |
