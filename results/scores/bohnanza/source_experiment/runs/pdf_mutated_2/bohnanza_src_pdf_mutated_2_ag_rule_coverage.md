# Rule coverage — assigned 4–5-player Ackerbohnen condition

Only `game_rules.pdf` supplies gameplay rules. `game_components.json` supplies observed names, counts, and printed Bohnometers; conflicts/gaps are recorded in `assumptions.json`.

| Supplied section / named rule | Implementing symbol(s) | Source-only probe / status | Assumption |
|---|---|---|---|
| Grundspiel (3–5 Spieler): Spielmaterial & Spielvorbereitung | `BEANS`, `COUNTS`, `Game.__init__`, `initial_state`, `PlayerState.fields` | 4/5-player guard; two fields; five individually dealt ordered cards; fixed start player | none |
| 104-card base composition and eight base sorts | `BEANS`, `COUNTS` | All eight names/counts audited below; variant replaces composition as directed | none |
| Hand order is immutable; first dealt is front and visible | `PlayerState.hand`, `plant_hand_front`, append-only draws | Only index 0 can be planted in phase 1; trades may use any index; received cards never enter hand | none |
| Draw pile, discard pile, coin pile | `GameState.deck`, `discard`, `PlayerState.coins`, `_draw_one`, `_harvest` | Explicit separate zones | none |
| Spielablauf; clockwise turns; fixed start-player card | `active`, `start_player`, four phase strings | Turn advances `(active + 1) % players`; start player never changes | none |
| Wichtige Regeln für den Bohnenanbau | `_plant_destinations`, fields as homogeneous lists | Empty or matching field only; same sort can occupy multiple fields | none |
| Phase 1: mandatory front card, optional second, never third | `phase1_must_plant`, `phase1_optional`, `phase1_planted`, `plant_hand_front` | Legal-action phase probe enforces 1 mandatory / at most 2; empty hand advances | none |
| Must harvest before an otherwise impossible planting | `_plant_destinations`, `harvest` actions in phases 1 and 3 | Harvest is exposed only when no destination exists during forced planting | none |
| Phase 2: reveal top two | `phase2_draw`, `draw_face_up`, `face_up` | Two sequential draws; third exhaustion can leave only one revealed card | none |
| Only active player trades with others | `phase2_trade`, `trade`, `gift` | Every transaction includes active player | A-02 |
| Any hand position may be traded; active may trade revealed cards | trade/gift action generation | All hand indices and face-up indices are offered | A-02 |
| Received/field cards cannot be retraded or put in hand | `pending`; action generation excludes `pending` and fields | Received cards remain pending until phase 3 | none |
| Unequal card counts; gifts require consent; both parties consent | repeated atomic `trade` / `gift` actions | Repeated transfers cover unequal totals; legal action represents mutual consent | A-02 |
| Phase 3: all traded and untraded revealed cards must be planted, order chosen | `end_trading`, `phase3`, `plant_pending` | Each player chooses among legal destination fields; pending cards are processed in received order | A-02 (source does not specify a representation for choosing arbitrary order) |
| Phase 4: active player draws three in order behind hand | `phase4`, `draw_remaining`, `draw_to_hand` | Exactly three sequential appends unless third exhaustion ends game | none |
| Die Bohnenernte; active-player harvesting | `_can_harvest`, `_harvest`; harvest actions | Active player harvests during own phases; a nonactive player may harvest only when forced to plant in phase 3 | none |
| Bohnenschutzregel | `_can_harvest` | A singleton cannot be harvested while any field has 2+ cards | none |
| Empty draw pile: reshuffle discard | `_draw_one`, `exhaustions` | First and second emptying recycle discard | none |
| Spielende: third emptying; special continuation in phase 2 | `_draw_one`, `ending_after_phase3`, `_finish_game` | Phase-2 exhaustion completes phases 2–3; phase-4 exhaustion ends immediately | none |
| Final harvest, hands ignored, card coins, winner/tie-break | `_finish_game`, `returns`, `winners` | All fields harvested; highest coins; farthest clockwise from start wins tie | none |
| Page 10 Variante-1 visible changes | phase 4 and third-exhaustion implementation | Active player alone draws 3; 4+ players end on third emptying | A-01 |
| Variante 2: Die Ackerbohnen — materials/setup | assigned `BEANS`, `COUNTS` | Eight base sorts + Weinbrandbohne + Ackerbohne; two fields | A-01 |
| Ackerbohne Bohnometer: exactly 2 grants third field, already owned grants nothing | `_harvest` Ackerbohne branch | Two cards append third empty field only if absent; both cards discarded, no coins | none |
| Ackerbohne Bohnometer: 3 grants 3 coins | `_harvest` Ackerbohne branch | Three-or-more branch pays 3; source deck contains only 3 | none |
| Flip board while retaining first/second fields | append-only third field in `_harvest` | Existing first and second lists remain in place | none |

## Named bean/card audit

| Name in supplied sources | Count / printed harvest implementation | Inclusion status |
|---|---|---|
| Blaue Bohne | `COUNTS` 20; `BOHNOMETER` 4/6/8/10 → 1/2/3/4 | included |
| Feuerbohne | 18; 3/6/8/9 → 1/2/3/4 | included |
| Saubohne | 16; 3/5/7/8 → 1/2/3/4 | included |
| Brechbohne | 14; 3/5/6/7 → 1/2/3/4 | included |
| Sojabohne | 12; 2/4/6/7 → 1/2/3/4 | included |
| Augenbohne | 10; 2/4/5/6 → 1/2/3/4 | included |
| Rote Bohne | 8; 2/3/4/5 → 1/2/3/4 | included |
| Gartenbohne | 6; 2/3 → 2/3 | included |
| Weinbrandbohne | 22; 4/7/9/11 → 1/2/3/4 | included by Variante 2 |
| Ackerbohne | 3; special 2-card field / 3 coins at 3 | included by Variante 2 |
| Kaffeebohne | observed 24; 4/7/10/12 → 1/2/3/4 | excluded: page 10 selects Weinbrand, not Kaffee |
| Kakaobohne | observed 4; 2/3/4 → 1/2/3 | excluded: page 10 selects Weinbrand, not Kakao |
| Elsterbohne | no component entry/Bohnometer supplied | excluded: page 3 says variants only and page 10 does not select it |
| Startspielerkarte | `start_player` | included as persistent state identity, not a bean/deck card |
| Übersichtskarte / Bohnenfeld-Ablage | phase API / `PlayerState.fields` | represented functionally, not shuffled cards |

The JSON also names Auftragskarten, AMIGO-Bohnentaler, and other Sonderkarten only to say they are not contained; none are introduced into the model.
