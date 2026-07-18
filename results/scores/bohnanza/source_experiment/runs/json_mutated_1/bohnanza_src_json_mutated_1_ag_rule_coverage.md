# Rule coverage

The implementation is the publisher-defined **Variante 2: Die Ackerbohnen (für 4–5 Spieler)**. It inherits Variante 1's altered phase 4/end condition and otherwise the Grundspiel. `Game(player_count=4|5)` selects either permitted count.

| Source section / named rule | Implementing symbol | Source-only probe / assumption |
|---|---|---|
| Cover / title | module docstring | Identity only; no mechanic. |
| Grundspiel (3–5 Spieler): Spielmaterial & Spielvorbereitung | `BEANS`, `Game.initial_state`, `Player` | Five ordered cards, two fields, start-player seat; A-02 for unspecified selection. Three-player layout is outside assigned 4–5 condition. |
| Eight Grundspiel beans and counts: Blaue, Feuer, Sau, Brech, Soja, Augen, Rote, Garten | `BEANS` | Counts and every printed Bohnometer threshold encoded. |
| Kaffee-, Weinbrand-, Kakao-, Acker-, Elsterbohnen note | `BEANS`; variant setup | Weinbrand and Acker included as publisher variant says; Kaffee/Kakao excluded and Elster has no supplied component data. A-01 audits observation conflict. |
| Deal five singly; hand order fixed / foremost card | `initial_state`, `Player.hand`, `plant_hand` | Deal loop and index-zero-only planting; trade may remove arbitrary cards without reordering survivors. |
| Draw/discard piles and four-player diagram | `GameState.deck`, `discard`, `_draw` | Fixed seeded shuffle supplies reproducible hidden information. |
| Spielablauf; clockwise active player; four phases | `phase`, `active`, `apply_action` | Explicit phase state machine. Start-player card has no further gameplay effect. |
| Important field rules: one type per field, same type on multiple fields, stack cards | `_plant_options`, field lists | Legal destinations enforce empty/matching type; multiple matching fields remain possible. |
| Phase 1: plant foremost, then optionally one more; no third | `plant_first`, `plant_second`, `finish_planting` | Legal-action probes expose required first and optional second only. Empty hand skips to phase 2. |
| Forced harvest when no field fits | harvest actions plus `_plant_options` | Plant is unavailable until a legal harvest creates a destination. |
| Phase 2: reveal exactly two, ownership, trade or plant | `reveal_two`, `market`, `trade` | Both revealed cards remain active-player controlled until traded, then untraded cards become incoming. |
| Example 1 (Soja/Blaue/Rote) | generic trade/field legality | Scenario is illustrative; generic symbols cover it. |
| Trade rules: active with others only; others not each other; any hand card; active may use revealed cards; no retrade; no field cards; unequal counts | `Offer`, offer-building actions, `incoming` | Incremental offer construction supports arbitrary finite bundles and gifts; acquired cards bypass hands so cannot be retraded. |
| Example 2 and agreement-before-removing warning | `submit_offer`, `accept_offer`, `reject_offer` | Cards move only on acceptance. |
| Traded cards placed sideways / never into hand | `Player.incoming` | Separate public planting queue represents sideways cards. |
| Example 3; gifts require consent | offers with empty request bundle | `submit_offer` requires at least one given card and recipient accepts/rejects. |
| End trading declaration | `finish_trading` | Available only with no pending offer. |
| Phase 3: everyone plants all traded/revealed cards, chosen order | `plant_incoming`, `_incoming_options` | Every incoming card is selectable at each planting decision. |
| Example 4 | generic `plant_incoming` | Both traded and revealed cards use same planting machinery. |
| Phase 4 Grundspiel draw three | superseded by Variante 1 for assigned condition | Not reachable in this source condition. |
| Die Bohnenernte; anytime; Bohnometer; coin cards; remainder discard; field empty | `_harvest_actions`, `_harvest`, `BEANS` | A-03 records interrupt ambiguity. Coin cards counted without retaining fronts. |
| Saubohne Bohnometer explanation and Example 5 Feuerbohne | generic `_harvest` | Threshold lookup yields described values. |
| Die Bohnenschutzregel | `_harvest_actions` | Singleton blocked iff another field has more than one; singleton harvest allowed otherwise. |
| Ein leerer Nachziehstapel | `_draw`, `empty_count` | Discard shuffled into new face-down deck whenever last card was drawn. |
| Grundspiel Spielende (third empty; finish phases 2/3; harvest; hand ignored; coins; tie) | `_draw`, `terminal_pending`, `returns` | Assigned variant keeps third empty for 4–5. Exhaustion during phase 2 finishes phases 2/3; returns harvest every field, ignore hands, and compare all coins. Tie A-04. |
| Variante 1: Drei neue Bohnensorten – Spielablauf | inherited state machine | Five-card start/four phases. Variant heading/setup page is not supplied; no missing bean identity is inferred. |
| Variante 1: each player draws one starting with active, clockwise | `draw_each`, `draw_one` | Explicit decision order; each draw appends to that player's ordered hand. |
| Variante 1 Spielende: 3 players second empty; 4+ third empty | `_draw` | Four/five path ends on third empty. |
| Variante 2 setup: base + Acker + Weinbrand, two fields | `BEANS`, `initial_state` | Publisher selection is 129 cards; conflict A-01. |
| Variante 2 follows Variante 1 | phase machine / draw and terminal symbols | Direct inheritance encoded rather than separate mode. |
| Ackerbohne Bohnometer differs; exactly two gives 2 coins plus third field; harvested Acker discarded | `_harvest` | Third field appended only on first qualifying two-card harvest; harvested surplus discarded. |
| Extra Ackerbohnen on first/second field move to corresponding side after board flip | `_harvest` / field representation | No extras can remain on the harvested field because the general harvest rule harvests the whole field; other fields remain in their corresponding list positions. |
| Already has third field: two Acker give nothing; three give normal 3 | `_harvest` | Explicit branch by field count and card count. |

## Component observation audit

`game_components.json` names all twelve beans and supplies counts/Bohnometers. Every named bean is listed here: Blaue Bohne, Feuerbohne, Saubohne, Brechbohne, Sojabohne, Augenbohne, Rote Bohne, Gartenbohne, Kaffeebohne, Weinbrandbohne, Kakaobohne, and Ackerbohne. The first eight plus Weinbrand and Acker are implemented for this publisher-defined condition. Kaffee and Kakao are audited but excluded. Its “all 157 simultaneously” statement conflicts with publisher setup and is recorded as A-01. Its absent Elsterbohnen, Auftrag cards, AMIGO coins, and other special cards are not introduced.
