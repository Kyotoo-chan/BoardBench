# Rule coverage — assigned 4–5-player source condition

Only `game_rules.pdf` and the observed component data listed by `SOURCE_MANIFEST.md` were used.

| Source section / named item | Implementing symbol | Source-only probe / status | Assumption |
|---|---|---|---|
| p2 Spielmaterial: field boards, start-player card, overview cards, 104 base cards and eight base types | `GameState.fields`, `active`, `BEANS`, `COUNTS` | initial-state inspection; overview/start card have no separate gameplay action | — |
| p2 base beans: Blaue, Feuer-, Sau-, Brech-, Soja-, Augen-, Rote, Gartenbohne | `BEANS`, `COUNTS`, `METER` | counts and every printed threshold transcribed from component observation | — |
| p2 note: Kakao, Weinbrand, Kaffee, Acker, Elster only in variants | variant deck constants | assigned variant includes only Weinbrand and Acker in addition to base | — |
| p3 setup; five individually dealt hand cards; order never changes; first dealt card is front; draw/discard piles | `initial_state`, ordered `hands`, `deck`, `discard` | initial state has five cards each and immutable tuple order | A-01 |
| p3 setup for four/five players: two fields | `initial_state` | each player starts with exactly two empty fields | — |
| p4 Spielablauf; active player and clockwise succession; start-player card stays | `active`, `_draw_and_advance` | turn advances `(active+1)%players`; start player remains player 0 | A-01 |
| p4 four phases in order | phases `plant_hand`, `trade`, `plant_trades`, `draw` | rollout traverses all four | — |
| p4 bean planting: same type per field; fields may be built simultaneously; cards overlap | `_plant_actions`, `_put_field` | incompatible planting requires harvest; matching type appends | — |
| p4 phase 1: first card mandatory, second optional, never third; planting starts/extends row | `plants_left`, phase-1 actions | legal-action probe exposes mandatory front card and optional skip only for second | — |
| p5 no hand cards at phase start skips to phase 2; lack of suitable field requires harvest | `FINISH_HAND_PLANTING`, `HARVEST_AND_PLANT_HAND` | empty-hand and incompatible-field paths represented | — |
| p5 phase 2: reveal top two cards; owned by active; trade or plant | `_reveal`, `face_up`, offer builder, `END_TRADING` | two cards move from deck to public face-up area | — |
| p5 trading: active player only; may trade all hand cards; other players cannot trade together | `trade`/`build_offer`, `current_player` | offers always have active player on one side | — |
| p5 active may trade both revealed cards; unequal card counts allowed; received cards cannot be retraded; field cards cannot trade | `Offer`, `_accept`, `pending` | incremental bundle permits unequal exchange; accepted cards enter pending, never hand | — |
| p6 agreement before removing hand cards | `SUBMIT_OFFER`, `ACCEPT_OFFER`, `_accept` | hand changes only on acceptance | — |
| p6 received cards lie crosswise beside fields and cannot enter hand | `pending` | accepted bundles remain pending until phase 3 | — |
| p6 gift is a trade form requiring recipient consent | one-sided `Offer`, `ACCEPT_OFFER` | submit permits either side to give cards without receiving cards | — |
| p6 active may continue with hand/revealed cards or end phase | repeated offers, `END_TRADING` | trade phase persists after acceptance/rejection | — |
| p7 phase 3: everyone plants traded cards; active also plants untraded revealed; owner chooses order | `pending`, `plant_trades` | each pending index is selectable; face-up remainder assigned active | — |
| p7 forced harvest before incompatible planting | `HARVEST_AND_PLANT_TRADED` | emitted when chosen field is incompatible and harvestable | — |
| p7 phase 4: active draws three one-by-one behind last hand card; left neighbor becomes active | `DRAW_THREE_CARDS`, `_draw_and_advance` | deck prefix appended without reordering existing hand | — |
| p7 harvesting only by active player (outside forced phase-3 planting) | `_voluntary_harvests`, phase gating | voluntary harvest exposed only in active trade phase | — |
| p7–8 Bohnometer, zero below threshold, harvested cards equal coins go face-down to coin pile, rest discard | `METER`, `_harvest`, `coins`, `discard` | threshold lookup uses greatest reached threshold and zero default | — |
| p8 harvest procedure and empty field afterward | `_harvest` | harvested field becomes empty | — |
| p8 Bohnenschutzregel: singleton field cannot be harvested if another field has more than one card | `_harvest_allowed` | protected singleton produces no harvest/harvest-and-plant action | — |
| p9 empty draw pile creates new draw pile in base game | not used in assigned Variant 2 | superseded by p10 variant end condition | — |
| p9 base game: third emptying, finish phases 2/3, all harvest, hands ignored, one coin/card, clockwise-nearest tie break | `_finish` reuses scoring/tie rules; third-emptying not used | terminal scoring probe harvests fields and ignores hands | A-02 |
| p10 Variant 1 (three players): three-card draw and second emptying | not implemented | outside assigned 4–5-player condition | — |
| p10 Variant 2 (four/five): base beans + Ackerbohnen + Weinbrandbohnen; two fields; otherwise Variant 1 flow | `BEANS`, `COUNTS`, `initial_state` | deck composition probe totals 129 cards and includes exactly ten named types | — |
| p10 Variant 2 end: first empty draw pile | `end_pending`, `_draw_and_advance`, `_finish` | first emptying leads to terminal resolution | A-02 |
| p11 Ackerbohne Bohnometer differs; harvest two grants third field, harvest three grants three coins; no reward for two if third already exists | `_harvest`, `third_field` | special branches cover 2/3 beans and already-owned case | — |
| Component observation: Weinbrandbohne (22), thresholds 4/7/9/11 → 1/2/3/4 | `COUNTS`, `METER` | constants exactly match observation | — |
| Component observation: Kaffeebohne, Kakaobohne | not used | explicitly excluded by assigned Variant 2 deck | — |
| Component observation: Ackerbohne (3), special printed rewards | `COUNTS`, `_harvest` | count and rewards represented | — |
| Component note: Elsterbohnen, orders, AMIGO coins, other special cards absent | not used | no symbols/actions for absent components | — |

The model exposes complete game state for framework inspection. Ordered hands are the private-information boundary; `render` deliberately reports only hand sizes.
