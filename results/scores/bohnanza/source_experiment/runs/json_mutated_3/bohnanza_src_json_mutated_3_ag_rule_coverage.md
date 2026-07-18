# Rule coverage — assigned 4–5-player base game

All probes are source-only inspections of the named symbol and are also exercised by `agentic_self_check.py` rollouts unless noted. Page numbers below are the printed rulebook pages (PDF image filename is one lower after the cover).

| Supplied section / named rule or card | Implementing symbol | Source-only probe / exclusion | Assumption |
|---|---|---|---|
| Spielmaterial & Spielvorbereitung; 4–5 players use two fields; starting-player card; five singly dealt hand cards; immutable order; draw/discard piles | `Game.initial_state`, `GameState.active`, `hands`, `deck`, `discard` | Inspect initial state: 4/5 players, 5 ordered cards each, 104-card base deck less deal | — |
| Eight base beans and counts: Blaue 20, Feuer 18, Saubohne 16, Brech 14, Soja 12, Augen 10, Rote 8, Garten 6 | `BEANS` | Sum counts = 104; exact labels preserved | — |
| Setup diagram / private hands | `GameState.hands`, `render` | Non-actor hands render only a count | — |
| Spielablauf: clockwise active player; four phases | `phase`, `active`, `apply_action` | Phase transitions and modulo player advance | — |
| Bohnenbau: one variety per field, same variety may occupy both, cards overlap | `_can_plant`, `_plant`, `fields` | Legal-action inspection for empty/same/different fields | — |
| Phase 1: mandatory front card, optional second front card, never third; empty hand skips | `plant_first`, `plant_second`, `plant_hand`, `skip_second`, `advance` | Legal-action inspection | — |
| Mismatching mandatory bean requires harvesting first | `_can_plant`, `_plant` | Plant transition harvests selected occupied field | — |
| Phase 2: reveal top two; they belong to active player; trade or plant | `_reveal_two`, `revealed`, `trade` | Transition after phase 1 | — |
| Handel: only active trades; others not with each other; any hand position; active may trade revealed; unequal counts permitted | `legal_actions` trade proposals | Atomic one-for-one and one-card gift actions can repeat, representing unequal multi-card exchanges | — |
| Both players consent; do not remove hand card before agreement | `proposal`, `accept_trade`, `reject_trade` | Proposal leaves holdings unchanged until accept | — |
| Received cards cannot be retraded or taken into hand; field cards cannot trade | `acquired`; trade action generation excludes it and fields | Legal-action inspection | — |
| Gifts require recipient consent | `propose_gift`, accept/reject | Proposal probe | — |
| Active ends trading | `end_trade` | Legal action always present in trade phase | — |
| Phase 3: all players plant traded/revealed cards, active must plant every revealed card; each chooses order | `plant_acquired`, actor sequence, pool choice | Every distinct pool bean/fitting field offered | — |
| Phase 4: active draws three, preserving order behind hand; next left player active | `draw_three` | Transition probe | — |
| Die Bohnenernte: harvest anytime, even when not active | `harvest` is offered to the current decision actor in every phase | Engine serializes decisions; a non-active actor can harvest whenever that player is the current phase-3/trade respondent. No asynchronous interrupt is representable by the required single `current_player` API | — |
| Bohnometer / count, flip paid cards to coin pile, discard remainder, field empty | `METER`, `_do_harvest`, `coins`, `discard` | Threshold boundary inspection | — |
| Blaue thresholds 4/6/8/10 → 1/2/3/4 | `METER` | Exact table probe | — |
| Feuer 3/6/8/9 → 1/2/3/4 | `METER` | Exact table probe | — |
| Saubohne 3/5/7/8 → 1/2/3/4 | `METER` | Exact table probe | — |
| Brech 3/5/6/7 → 1/2/3/4 | `METER` | Exact table probe | — |
| Soja 2/4/6/7 → 1/2/3/4 | `METER` | Exact table probe | — |
| Augen 2/4/5/6 → 1/2/3/4 | `METER` | Exact table probe | — |
| Rote 2/3/4/5 → 1/2/3/4 | `METER` | Exact table probe | — |
| Garten 2/3 → 2/3 (no other printed reward) | `METER` | Exact table probe | — |
| Bohnenschutzregel: singleton cannot harvest if another field has 2+ | `_harvest_allowed` | Legal-action and rejection probe | — |
| Empty draw pile: shuffle discard into new face-down draw pile | `_draw_one` | Exhaustion transition probe | — |
| Third emptying ends; if during phase 2, finish phases 2 and 3 | `_draw_one`, `_reveal_two`, `pending_end`, `finish_acquired` | Exhaustion transition probe | A-01 |
| End: harvest all fields, hand ignored, highest coins; tie farthest clockwise from start | `returns` | Terminal score probe adds both fields' Bohnometer value to stored coins and excludes hands | A-02 |
| Cover/title and examples 1–5 | Labels/UI only; mechanics covered above | Examples are explanatory, not separate combinations | — |
| Page 10 Variante 1: three new bean types, draw one each, different end count | Not implemented: outside assigned base 4–5 condition | Audited exclusion | — |
| Kaffeebohne, Weinbrandbohne, Kakaobohne and Elsterbohne note | Not implemented: variants only; page 2 expressly says only variants | Audited exclusion | — |
| Variante 2 Ackerbohnen (4–5), 157-card component observation, special Acker harvest/field-return rule | Not implemented: optional variant outside assigned base condition | Audited exclusion; component observation does not override base gameplay | — |

## Explicit source limitation

The required API supplies only one current decision maker, so truly asynchronous “harvest at any time” interrupts cannot be exposed for every player between every atomic decision. Harvest is exposed to whichever player is currently deciding, including non-active trade respondents and phase-3 planters (A-03). This serialization is documented rather than filled from outside knowledge.
