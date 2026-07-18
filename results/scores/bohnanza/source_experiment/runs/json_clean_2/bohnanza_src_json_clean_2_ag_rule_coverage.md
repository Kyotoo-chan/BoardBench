# Rule coverage — Ackerbohnen variant (4–5 players)

| Source section / named item | Implementing symbol | Source-only probe or limitation | Assumption |
|---|---|---|---|
| p2 Spielmaterial & Vorbereitung; 104 base cards; 6/8/10/12/14/16/18/20 | `BEANS`, `COUNTS`, `initial_state` | constants and five-card deal | — |
| p2 Startsplayer, fields, taler area, overview cards | `active`, `fields`, `coins` | four-player initial state | A-01 |
| p3 shuffle, deal singly, immutable hand order, draw/discard | `initial_state`, front index 0, `_draw` | hand planting always removes index 0 | A-03 |
| p4 Spielablauf / clockwise active player / four phases | `phase`, `active`, `_finish_turn` | self-check traverses transitions | — |
| p4 bean-field rules: one kind per field; same kind on multiple fields; contiguous rows | `_can_plant`, planting actions, list fields | legal actions only target empty/same-kind fields | — |
| p4 phase 1 mandatory first, optional second, no third | `plant_first`, `plant_second` | first phase has no finish while hand nonempty | — |
| p5 empty hand skips phase 1 | `legal_actions` | `finish_plant` only action | — |
| p5 phase 2 reveal two and own them | `finish_plant`, `revealed` | exactly two `_draw` calls | — |
| p5–6 trade rules: active trades with all; others not together; hand order irrelevant; revealed usable; received not retraded/on hand; unequal counts; gifts need consent | offer/respond actions, `acquired`, `pending` | accept/reject and sequential gifts/trades | A-02 |
| p7 phase 3 all received/revealed planted; owner chooses order | `plant_acquired`, actor scan | mandatory until acquired list empty; list order is acquisition order (order-choice gap) | A-02 |
| p7 phase 4 basic draw three | superseded by variant rule | not implemented for assigned condition | — |
| p7–8 Die Bohnenernte; anytime; meter; empty after harvest | `harvest`, `_coin_value` | harvest appears in every nonterminal phase for current actor | — |
| p8 Taler cards to coin pile, remainder discard | abstracted by `coins` and `discard` | exact coin-card identities not retained | — |
| p8 Bohnenschutzregel | `_protected` | singleton blocked when another field has >1 | — |
| p9 empty draw pile: recycle discard | `_draw` | increments exhaustion and recycles before third | — |
| p9 Spielende: third exhaustion; finish phases 2/3; harvest all; hands ignored; most coins; clockwise tiebreak | `_draw`, `_finish_turn`, `returns` | returns expose coin totals; caller can apply stated comparison/tiebreak | — |
| p10 variant phase 4: each player draws one, active first clockwise | `_finish_turn` | offset loop appends one each | — |
| p10 variant end: third exhaustion for 4+ | `_draw`, `_finish_turn` | threshold 3 | — |
| p10 Variante 2 materials: all base + Ackerbohnen + Weinbrandbohnen; two fields | `BEANS`, `COUNTS`, `fields` | deck has 129 cards, two initial fields | — |
| p11 Ackerbohne Bohnometer differs; two = third field; harvested Acker discarded | Acker branch in `harvest` | two adds third only if absent; cards discarded | — |
| p11 two Acker with third field already = nothing; three Acker = 3 taler | Acker branch in `harvest` | explicit `n==2`/`n>=3` branches | — |
| Named base beans: Blaue, Feuer, Sau, Brech, Soja, Augen, Rote, Garten | `BEANS`, `COUNTS`, `METER` | component-observation thresholds encoded | — |
| Named variant beans: Weinbrand, Acker | `BEANS`, `COUNTS`, `METER`, special harvest | included; Kaffee/Kakao/Elster excluded as directed by variant | — |

The printed harvest thresholds are supplied most legibly by `game_components.json`, which the manifest permits for printed Bohnometer values. `returns` intentionally reports final coin totals rather than normalising winners; this preserves ties and the rulebook's clockwise tie-break information.
