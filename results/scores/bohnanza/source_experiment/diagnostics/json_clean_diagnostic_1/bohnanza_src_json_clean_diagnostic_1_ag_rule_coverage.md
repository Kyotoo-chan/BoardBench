# Rule coverage

The implementation is source-bounded to the supplied 4-player instance of the 4–5 player **Variant 2: Die Ackerbohnen**. `BEANS`, `GameState`, and `Game` are the principal implementing symbols. The required self-check supplies generic probes; the source-only probes below are direct code/state probes suitable for a focused test suite.

| Supplied section / named rule | Implementing symbol | Source-only probe / limitation | Assumption |
|---|---|---|---|
| Spielmaterial & Spielvorbereitung; 104 Grundspiel cards; 3 players get 3 fields, 4–5 get 2; start-player card; five ordered cards; draw/discard piles | `BEANS`, `initial_state`, `GameState` | Assert 4 players, two fields, five cards and stable hand order. Physical player mats/start card are represented by indices/`active`. | A-01 |
| Eight Grundspiel beans: Blaue (20), Feuer (18), Sau (16), Brech (14), Soja (12), Augen (10), Rote (8), Garten (6) | `BEANS` | Assert counts and thresholds equal component observation; all are in variant deck. | — |
| Note: Kakao, Weinbrand, Kaffee, Acker, Elster only in variants | variant deck construction | Weinbrand and Acker included per Variant 2; Kaffee/Kakao/Elster excluded. | — |
| Hand order may never change; first dealt card is front | `initial_state`, `plant_hand` | Only index 0 can be planted; trades may select any hand card without reordering remainder. | — |
| Spielablauf clockwise; start card stays; four phases | `phase`, `active`, `actor`, `apply_action` | Roll through plant, flip/trade, plant traded, clockwise draw, next active. | — |
| Bohnenanbau: one type per field; same type may occupy several fields; cards overlap | `_plant`, `legal_actions` | Plant action exists only for empty/matching fields. | — |
| Phase 1 mandatory front card, optional second; empty hand skips | `legal_actions`, `apply_action` | Check mandatory first, skip only second, and `skip_empty_hand`. | — |
| Must harvest before planting an incompatible bean with no field | harvest actions plus planting legality | Plant is absent until a legal field is harvested. | — |
| Phase 2 reveal top two; they belong to active; may plant or trade | `flip_two`, `table`, trade actions, `end_trade` | Flip creates two visible table cards; leftovers go to active's `traded`. | A-03, A-04 |
| Trade only active with others; any hand cards; active may trade revealed; received cards cannot be retraded or put in hand; unequal trades allowed | `trade_table_for_hand`, `trade_hands`, `give_table`, `traded` | Partners never trade directly; received cards enter `traded`; gifts and 1-for-1 are probed. Unequal multi-card bundles can be composed, though consent is atomic. | A-03 |
| Gift requires consent | atomic trade/gift action | A legal gift denotes the completed consensual gift. | A-03 |
| Phase 3 everyone plants all received/revealed cards in chosen order; harvest first if necessary | `plant_traded`, `done_traded`, harvest actions | Every pending-card index is exposed; `done_traded` only exists when none remain. | A-03 |
| Phase 4 Grundspiel draws three; variant draws one each clockwise starting active | `draw_one`, `draw_left` | Assert exactly four draws in the implemented 4-player condition. | A-01, A-02 |
| Die Bohnenernte: may harvest any time, including inactive; Bohnometer coins; paid cards turn coin-side, remainder discarded; field empties | harvest actions, `_do_harvest` | Harvest actions are exposed for every player's eligible fields in every phase. | — |
| Bean protection: a singleton cannot be harvested if any field has >1 | `_harvestable` | Construct singleton plus pair and assert singleton harvest absent. | — |
| Empty draw pile: shuffle discard into new facedown deck | `_draw` | Exhaust deck and assert discard becomes deck and `empty_count` increments. | — |
| Spielende: third emptying; finish phases 2/3 if during reveal; harvest fields; hand ignored; most coins; clockwise-furthest tied player from start wins | `_draw`, `_finish`, `returns` | Force third emptying, check terminal has no actions and tie picks greatest index. | A-04 |
| Variant 1 visible rules: five starting cards; each player draws one clockwise; 3 players end on second emptying, 4+ on third | `initial_state`, `draw_one`, `_draw` | Four-player branch uses third emptying. Unavailable Variant-1 text cannot be audited. | A-02 |
| Variant 2 material: Grundspiel + Weinbrandbohnen + Ackerbohnen; 4–5 players; two fields | `BEANS`, `initial_state` | Assert deck composition totals the ten listed types and all start with two fields. | A-01, A-02 |
| Die Bohnenernte (Acker): distinct meter; exactly two grants third field and no coins; harvested cards discarded; existing third field gives nothing; exactly three gives 3 coins; later Acker on first/second field transfers to third field | `_do_harvest` | Probe 2-card grant/no-grant and 3-card/3-coin outcomes. Transfer-back instruction is not modeled because normal planting already permits multiple Acker fields and the timing/mandatory nature is not fully specified. | A-02 |

## Component observation audit

`game_components.json` additionally names Kaffeebohne (24: 4/7/10/12), Weinbrandbohne (22: 4/7/9/11), Kakaobohne (4: 2/3/4), and Ackerbohne (3 special), and says Elsterbohnen and special cards are absent. Kaffee and Kakao are observed but excluded by the assigned Variant-2 material instruction. Weinbrand and Acker are implemented. The Grundspiel and Weinbrand printed Bohnometers are encoded in `BEANS`; Acker's special harvest is encoded in `_do_harvest`.
