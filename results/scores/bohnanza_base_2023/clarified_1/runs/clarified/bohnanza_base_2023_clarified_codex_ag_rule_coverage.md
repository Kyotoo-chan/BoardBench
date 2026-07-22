# Rule coverage

The publisher rulebook is the game-rule source. The four entries in `clarifications.json` are used only where the packet manifest explicitly authorizes their identified interpretation or transcription. Contract/profile fields are representation only.

| Source section or named rule | Implementing symbol(s) | Probe or reason not probed | Assumption |
|---|---|---|---|
| Spielidee | `Game.returns`, planting/harvest flow | Terminal scoring and rollout probes in self-check | A-03 only for tie ordering |
| Spielmaterial & Spielvorbereitung; 104 cards; 6/8/10/12/14/16/18/20 | `BEANS`, `COUNTS`, `initial_state` | Initial inventory/count and seeded-repeatability probes | A-01, A-02 |
| 3 players use 3 fields; 4–5 use 2 | `initial_state` | Constructors for 3, 4, 5; fixture check covers 5 | None |
| Five hand cards; hand order fixed; front card visible; no sorting | `initial_state`, hand lists, `observation_to_data`, plant actions restricted to index 0 | Plant legal-action probe and opponent-hidden observation probe | A-02 for dealing order |
| Deck/discard/coin piles and clockwise active player | `GameState.zones`, `draw`, `initial_state` | Rollout and serialization probes | A-01 |
| Four phases | `PHASES`, `legal_actions`, `apply_action` | Random rollouts and phase fixtures | None |
| Same bean per field; same type may occupy several fields; cards overlap | `_plant_fields`, plant transition | Source-only compatible/incompatible-field probes | None |
| Phase 1: mandatory front card, optional second, third forbidden; empty hand skips | `legal_actions`, plant/pass transitions | Legal action probes for empty/one/two card hands | None |
| Bean harvest required when no field can accept a mandatory plant | harvest actions plus absence of plant until a field is cleared | Source-only blocked-plant probe | None |
| Phase 2: reveal top two; only active player trades; all hands plus active revealed cards; received/field cards excluded | reveal and trade branches of `legal_actions` | Source-only ownership/zone trade probes | None |
| Any unequal trade quantities; mutual consent; remove only on acceptance | `trade_propose`, `trade_response`, `_remove_refs` | 1:2 and 3:1 source-clarification probes | CLAR-TRADE-01 |
| Gifts require recipient consent | gift proposal and accept/reject transitions | Gift accept/reject probe | None |
| Traded cards lie beside fields and cannot re-enter hand | `zones.pending_received` | Observation and transition probe | None |
| Phase 3: every recipient plants all received cards, in chosen order; active also plants untraded revealed cards | `plant_received`, `_set_next_recipient`, indexed received plant actions | Multi-player and ordering probes | CLAR-PHASE3-01 |
| Phase 4: active draws three behind hand, then clockwise successor | draw transition | Rollout/hand-order probe | None |
| Die Bohnenernte; harvest any time; beanometer payouts; rotate paid cards as coins; discard remainder; field empties | `_harvest_actions`, `_payout`, harvest transition | Threshold boundary probes for all eight cards | CLAR-PAY-01 transcribes card graphics |
| Bohnenschutzregel: a singleton cannot be harvested if any field has 2+ | `_harvest_actions` | Singleton protected/unprotected probes | None |
| Ein leerer Nachziehstapel: shuffle discard and form new deck | `_draw_one` | Depletion/recycle source-only probe | None |
| Third empty deck; special Phase 2 completion through Phase 3; no Phase 4 | `_draw_one`, `_set_next_recipient` | Depletion during reveal versus draw probes | CLAR-END-01 |
| End scoring: one coin per coin-card; hand ignored; clockwise-farthest-from-start tie winner | `returns` | Terminal fixture scoring probes | A-03 |
| Canonical state/action/observation representation | serialization methods | `agentic_self_check.py`, `profile_fixture_self_check.py` (representation only) | Not a game rule |

All eight named bean cards are covered by `BEANS`, `COUNTS`, and `THRESHOLDS`; no other named card or combination appears in the supplied base-game rulebook.
