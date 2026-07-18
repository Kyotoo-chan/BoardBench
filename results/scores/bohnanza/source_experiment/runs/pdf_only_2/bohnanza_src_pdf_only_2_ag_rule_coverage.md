# Rule coverage

The implemented playable condition is the **Grundspiel for 4–5 players**, defaulting to four. Page references use the printed rulebook pages (PDF image filenames are one lower after the cover). All probes are source-only: direct state construction or public API behavior, with no external rule assumptions.

| Supplied section / named rule | Implementing symbol | Source-only probe or exclusion | Assumption |
|---|---|---|---|
| Cover / title | module docstring | Identity only; no mechanic | — |
| Grundspiel (3–5 Spieler): Spielmaterial & Spielvorbereitung | `Game.__init__`, `Game.initial_state`, `BASE_COUNTS` | 4/5 accepted; two fields and five ordered cards each; 104-card distribution minus deal | — |
| Startspielerkarte; clockwise order; card not passed | `start_player`, `active`, phase-4 transition | start is 0 and active advances modulo player count while start stays 0 | — |
| Eight bean sorts/counts: Gartenbohne 6, Rote Bohne 8, Augenbohne 10, Sojabohne 12, Grüne Bohne 14, Saubohne 16, Feuerbohne 18, Blaue Bohne 20 | `BASE_COUNTS` | count constructed deck before deal | — |
| Kakao-, Weinbrand-, Kaffee-, Acker-, Elsterbohnen only in variants | variant gate in `initial_state` | base deck excludes every named variant bean | A-03 |
| Deal individually five; immutable hand order/front card | `initial_state`, phase-1 `legal_actions`/`apply_action` | only index 0 can be planted; phase-4 appends in draw order | — |
| Four phases / active-player sequence | `phase`, `legal_actions`, `apply_action` | phase state machine follows 1→2→3→4 | — |
| Wichtige Regeln für den Bohnenanbau: one sort per field; same sort on several fields | `_plant_actions` | target offered iff empty or matching; all matching fields offered | — |
| Phase 1: first mandatory, second optional, never third; empty hand skips | phase-1 branches | first lacks skip when hand nonempty; second has skip; transition after second | — |
| Required planting with no suitable field requires harvest | `_plant_actions`, `_harvest_actions` | only harvest actions remain until a field is emptied | — |
| Phase 2: reveal top two; revealed belong to active player | `_begin_trade`, `revealed` | two draws enter public revealed list | A-01 at third exhaustion |
| Only active trades with others; others not mutually | `start_offer`, `offer_partner` | every offer includes active and exactly one other player | — |
| Trade any hand position; active may trade revealed cards | offer-build actions | every uncommitted hand index and revealed index is offered | — |
| Received cards cannot be retraded and are placed beside fields, not in hand | `received`, `accept_offer` | accepted cards enter received only; offer builder never reads received | — |
| Field cards cannot be traded | offer builder | only hands and active revealed list are sources | — |
| Unequal quantities permitted | incremental offer builder | either side can add any number; submission needs at least one card | — |
| Both players consent; do not remove hand card early | `submit_offer`, `trade_response`, `accept_offer` | cards remain in place until partner accepts | — |
| Gifts permitted and recipient may refuse | one-sided offer plus accept/reject | submission permits one side empty | — |
| Trading may continue after revealed cards traded | return to `trade` after acceptance | `end_trade` remains optional after each deal | — |
| Phase 3: all received and untraded revealed cards must be planted; owner chooses order | `end_trade`, `pending`, phase-3 actions | all cards queued and no finish action until empty | Queue is stable by player/source; each owner chooses fields, but the UI does not offer arbitrary reordering of its pending cards (nonmaterial where planting legality is resolved card-by-card). |
| Phase 4: active draws three sequentially behind hand; left player becomes active | `draw_phase4` | cards append and active increments | A-01 |
| Die Bohnenernte: harvest any time, including inactive player | `_harvest_actions` in every decision state | off-turn field harvest actions present | A-02 |
| Printed Bohnometers for all eight base beans | `METERS`, `_coins_for` | boundary counts map to printed rewards | — |
| Harvest steps: count, flip reward cards to coins, discard rest, empty field | `_harvest` | coins rise by meter; discard rises by non-coin cards; field clears | Coin cards are represented by an integer because their bean face never returns to play. |
| Example 5: three Feuerbohnen yield one coin, two discarded | `METERS["Feuerbohne"]`, `_harvest` | direct three-card field probe | — |
| Bohnenschutzregel | `_harvest_actions` | singleton excluded iff another own field has more than one | — |
| Empty draw pile: recycle shuffled discard; third empty ends | `_draw_one`, `exhaustions` | first two exhaustion events recycle; third returns no card | A-01 |
| Spielende; phase-2 exhaustion finishes phases 2/3; final harvest; hands ignored; one coin per card | `end_after_phase3`, `_finish` | forced phase-3 completion then all fields score; hands untouched | A-01 |
| Winner most coins; tie clockwise farthest from start | `_finish`, `returns` | tied index with greatest clockwise distance selected | — |
| Variante 1: Drei neue Bohnensorten; each player draws one in phase 4; 3-player alternate ending | recognized as `variant="three_new"` | not playable: supplied pages omit its setup bean identities/counts/meters; 3-player rule is outside assigned 4–5 condition | A-03 |
| Variante 2: Die Ackerbohnen (für 4–5 Spieler): base sorts plus Acker/Weinbrand, two fields; flow as Variante 1 | recognized as `variant="Ackerbohnen"` | not playable: Weinbrand and complete Acker component counts/meters are absent | A-03 |
| Ackerbohne harvest: two grants third field if absent (no coins), three grants three coins; preserve fields 1/2 on flip | `METERS["Ackerbohne"]` documents visible coin threshold | transition excluded because variant cannot be initialized from complete supplied data | A-03 |

## Public API coverage

`GameState` and `Game` expose `initial_state`, `current_player`, `legal_actions`, `apply_action`, `is_terminal`, `returns`, `render`, `action_to_name`, and `name_to_action`. Terminal states expose no actions. Action labels retain source terms such as “Bohnenernte,” “Bohnenkarte anbauen,” and “Bohnenkarten nachziehen”; the JSON suffix makes every name unique and exactly reversible.
