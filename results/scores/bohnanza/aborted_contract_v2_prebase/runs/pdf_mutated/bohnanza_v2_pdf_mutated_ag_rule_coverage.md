# Rule coverage — Ackerbohnen variant (4–5 players)

The publisher PDF is the gameplay authority. `game_components.json` is used only for observed card counts and printed Bohnometers where the PDF identifies the included sorts but its small card images are not legible as text.

| Source section / named rule | Implementing symbol | Source-only probe / audit | Assumption |
|---|---|---|---|
| Grundspiel: Spielmaterial & Spielvorbereitung | `COUNTS`, `Game.initial_state` | 4/5 players; two fields; five cards dealt singly; remaining shuffled deck | none |
| Hand order (first dealt is front; never reorder) | `Player.hand`, `plant_first`, phase-4 append | front is index 0; draws append in order; no `reorder_hand` legal action | none |
| Four phases / clockwise active player / fixed start player | `phase`, `apply_action(draw)` | phase progression and `(active+1)%N` | none |
| Important planting rules | `_can_plant`, `_plant_actions` | same sort per field; same sort may occupy multiple fields | none |
| Phase 1: mandatory first, optional second, never third | `legal_actions`, `apply_action(plant/pass)` | first uses hand[0], second has pass, then reveal | none |
| Empty hand skips phase 1 | `legal_actions(plant_first)` | sole pass action | none |
| Must harvest if no suitable field | `_plant_actions`, `_harvest_actions` | harvest enables planting; protected-field restriction applied | A-02 for non-active phase-3 recipient |
| Phase 2: reveal two | `_draw_one`, `apply_action(reveal)` | sequential draws, including partial reveal at third depletion | none |
| Only active player trades; cards anywhere in hand; active may use revealed cards | `legal_actions(trade)`, `gift_propose` | owners/zones/indexes represented; opponents cannot initiate | A-02 |
| Traded cards cannot be retraded or put in hand; field cards cannot trade | `pending_received`, `_execute_exchange` | received cards leave trade zones and remain face-up pending | none |
| Unequal-card trades | `trade_start`, add-offer/request actions, `trade_submit` | proposal permits arbitrary positive card counts on each side | none |
| Gifts require recipient consent | `gift_propose`, `gift_accept`, `gift_reject` | explicit response state | none |
| Phase 3: all received and untraded revealed cards planted, any order | `pending_received`, `plant_received`, `_select_planter` | every pending card must be planted before draw | none |
| Phase 4: active player draws three in order | `apply_action(draw)` | sequential append behind last hand card | A-01 only on third depletion |
| Harvest: only active player; Bohnometer; coin cards removed; remainder discard; empty field | `_harvest_actions`, `_harvest`, `METERS` | values audited for every included bean below | A-02 narrow forced phase-3 exception |
| Bohnenschutzregel | `_harvest_actions` | singleton field illegal if any own field has >1 card | none |
| Empty deck / reshuffle discard | `_draw_one` | depletion counter and deterministic reshuffle | none |
| Third depletion; reveal exception; final harvest; hands ignored | `_draw_one`, `_finish` | phase-2 completion flag, all fields harvested | A-01 |
| Winner and tie-break | `returns` | most coins; farthest clockwise from fixed start player | none |
| Variante 2: Die Ackerbohnen (4–5 Spieler) | `Game.__init__`, `BEANS`, `COUNTS` | exactly eight base sorts + Weinbrandbohne + Ackerbohne; two fields | none |
| Variant flow refers to Variante 1 | phase implementation | five-card setup, familiar four phases, active draws three, four-plus ends on third depletion | none |
| Ackerbohne harvest: exactly two grants third field, cards discarded | `_harvest` | flips state to three fields and preserves old first/second fields | none |
| Two Ackerbohnen with existing third field give nothing | `_harvest` | cards discarded; no coins or field change | none |
| Three Ackerbohnen give three coins | `METERS`, `_harvest` | threshold `(3,3)` | none |
| Blaue Bohne (20): 4/6/8/10 → 1/2/3/4 | `COUNTS`, `METERS` | component observation audited | none |
| Feuerbohne (18): 3/6/8/9 → 1/2/3/4 | `COUNTS`, `METERS` | component observation audited | none |
| Saubohne (16): 3/5/7/8 → 1/2/3/4 | `COUNTS`, `METERS` | PDF page 9 example plus component audit | none |
| Brechbohne (14): 3/5/6/7 → 1/2/3/4 | `COUNTS`, `METERS` | component observation audited | none |
| Sojabohne (12): 2/4/6/7 → 1/2/3/4 | `COUNTS`, `METERS` | component observation audited | none |
| Augenbohne (10): 2/4/5/6 → 1/2/3/4 | `COUNTS`, `METERS` | component observation audited | none |
| Rote Bohne (8): 2/3/4/5 → 1/2/3/4 | `COUNTS`, `METERS` | component observation audited | none |
| Gartenbohne (6): 2/3 → 2/3 | `COUNTS`, `METERS` | component observation audited | none |
| Weinbrandbohne (22): 4/7/9/11 → 1/2/3/4 | `COUNTS`, `METERS` | included by variant; component observation audited | none |
| Ackerbohne (3): 2 → third field, 3 → 3 coins | `COUNTS`, `_harvest`, `METERS` | PDF page 11 and component observation agree | none |
| Excluded named variant beans: Kaffee-, Kakao-, Elsterbohnen | absent from `BEANS` | variant explicitly selects base + Weinbrand + Acker | none |

Canonical state/action/observation serialization is implemented by `state_to_data`, `state_from_data`, `action_to_data`, `action_from_data`, and `observation_to_data`; opponent hands are represented only by size in observations.
