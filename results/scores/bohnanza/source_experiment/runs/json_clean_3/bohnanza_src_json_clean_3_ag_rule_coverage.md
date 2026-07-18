# Rule coverage — assigned 4–5-player Variant 2

All probes are source-only inspections of `game_rules.pdf`/page images and `game_components.json`.

| Supplied section / named item | Implementing symbol | Probe / limitation | Assumption |
|---|---|---|---|
| Grundspiel: material/setup; 4–5 players use two fields; five singly dealt ordered hand cards; fixed start player | `Game.initial_state`, `GameState.field_counts`, ordered `hands` | Initial state has 2 fields and 5 cards/player; deal loop preserves receipt order | — |
| 104-card base material and eight names/counts | `BEANS` | Counts audited: Garten 6, Rote 8, Augen 10, Soja 12, Brech 14, Sau 16, Feuer 18, Blaue 20 | Variant 2 changes deck; A-01 |
| No hand sorting / front card visible | tuple `hands`, `plant_front` | Only index 0 is plantable; trades remove in-place without sorting | — |
| Four phases / clockwise active player | `phase`, `active`, `apply_action` | State transitions cover phases 1–4 and advance active clockwise | — |
| Bean planting: one variety per field; same variety on multiple fields | `legal_actions` planting branches | Empty or same-type fields offered; no uniqueness restriction between fields | — |
| Phase 1: first front card mandatory, second optional, never third; empty hand skips | `first_planted`, `plant_front`, `finish_hand_planting` | Finish absent before first plant unless hand empty; present after second | — |
| Must harvest when no compatible field | harvest actions plus absence of plant action | Player can harvest then plant; engine exposes all anytime harvests too | — |
| Phase 2: reveal top two; active owns them | `_draw`, `face_up`, `finish_hand_planting` | Two sequential draws, including partial draw at exhaustion | — |
| Trade: only active with others; any hand position; active may use face-up; no field cards; unequal bundles | offer builder (`begin_offer`, `add_give`, `add_ask`, `propose_offer`) | Incremental multiset construction represents arbitrary nonempty give and any ask | — |
| Received cards cannot be retraded or put in hand | `received`; trade pools exclude it | Accepted cards enter sideways received area only | — |
| Both parties consent; do not remove early | `respond`, `accept_offer`, `reject_offer` | Cards transfer only on accept | — |
| Gifts require recipient consent | empty `offer_ask` is legal; response actions | Nonempty give/empty ask round-trips as a gift | — |
| Active may keep trading after face-up cards traded; active ends phase | `trade`, `finish_trading` | Hand remains tradable; explicit finish | — |
| Phase 3: all received and active's untraded face-up cards mandatory; free order | `plant_received`, actor rotation | Any remaining type can be selected; finish only once that actor has none | — |
| Phase 4 base rule (three cards active) | not active under assigned condition | Superseded by Variant-1 draw rule | — |
| Harvest anytime, including nonactive | harvest actions generated for every player in every nonterminal phase | Legal action enumeration probes all players | — |
| Bohnometer; reward cards to coin pile, rest discard; field empties | `BEANS`, `_harvest` | Threshold tables audited against component observation; coin count increments, remainder discarded | — |
| Bohnenschutzregel | `_harvestable` | Singleton blocked iff another own field has >1 card | — |
| Empty deck: recycle shuffled discard | `_draw` | First/second exhaustion refills when discard exists | — |
| Spielende: third exhaustion; phase-2 exhaustion finishes phases 2–3; final harvest; hands ignored | `_draw`, draw/phase transitions, `_finish_game` | Phase 2 continues with available revealed cards; draw-round third exhaustion finishes immediately | — |
| Winner most coins; tie farthest clockwise from fixed start player | `returns` | Highest tied player index wins because start player is index 0 | A-03 (utility encoding only) |
| Variante 1 visible Spielablauf: everyone draws one clockwise; 4+ ends on third exhaustion | `draw_round`, `draw_one`, `draw_left` | Exactly players draws, active first, clockwise | A-02 |
| Variante 2 setup: 4–5; base varieties + Acker + Weinbrand; two fields | `Game.__init__`, `BEANS`, `initial_state` | Constructor rejects other counts; deck totals 129 | A-01 |
| Ackerbohne harvest: exactly two grants third field, cards discard; already has third gives nothing | `_harvest`, `field_counts` | Two-card branch grows 2→3 only and gives 0 coins | — |
| Ackerbohne board flip preserves first/second fields | `_harvest` appends an empty third field | Existing field tuples remain in positions 0/1 | — |
| Ackerbohne three cards gives three coins | `_harvest` | `n >= 3` awards 3; only three Acker cards exist | — |
| Named component-only beans Kaffeebohne, Kakaobohne | not in assigned Variant-2 deck | Audited counts/Bohnometers in component observation; rulebook says variant-only, Variant 2 does not select them | — |
| Named but unobserved Elsterbohne and special cards | not implemented | Rulebook mentions variant-only Elster; component source says it and other specials are absent | — |
| Weinbrandbohne | `BEANS["Weinbrandbohne"]` | 22 cards; thresholds 4/7/9/11 → 1/2/3/4 from component observation | — |
| All base named Bohnometers | `BEANS` | Each threshold table transcribed from `game_components.json`; page 8 independently illustrates Saubohne | — |

## Explicit model boundary

The source describes free-form negotiation but no communication protocol. The engine models the rule-relevant outcome as an incrementally constructed offer followed by explicit acceptance/rejection. Private hands remain separate in state, while `render` is a referee/debug view rather than a player observation API.
