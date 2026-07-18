# Rule coverage — Grundspiel, 4–5 players

Only the publisher rulebook is used. The cover (page 1) has no mechanics.

| Source section / named rule or bean | Implementation symbol | Probe / note | Assumption |
|---|---|---|---|
| Spielmaterial & Spielvorbereitung (pp.3–4): 104 cards, 8 sorts, two fields, five ordered hand cards, start player, deck/discard | `BEANS`, `COUNTS`, `Game.initial_state`, `GameState` | Counts sum to 104; initial state inspection | A-02 shuffle API |
| Gartenbohne (6), Rote Bohne (8), Augenbohne (10), Sojabohne (12), Brechbohne (14), Saubohne (16), Feuerbohne (18), Blaue Bohne (20) | `BEANS`, `COUNTS`, `METERS` | constants/source-only meter probes | none |
| Most important rule: hand order fixed, foremost card visible | index zero operations in `plant_hand`, draws append | plant/draw transition probe | none |
| Spielablauf; clockwise active player; start card stays | `active`, `finish_building` | four/five turn wrap probe | none |
| 1. Phase: plant first mandatory, second optional, no third; same sort per field, same sort may occupy both | `plant_first`, `plant_second`, `_can_plant` | legal-action probes | none |
| Forced harvest before incompatible planting | standalone `harvest` plus `_can_plant` | blocked-plant probe | none |
| Empty hand skips directly to phase 2 | `skip_empty_hand` | empty-hand probe | none |
| 2. Phase: reveal two; they belong to active player; trade with all, others not mutually; hand position irrelevant; revealed cards tradable; acquired/field cards not retradable; unequal trades and gifts; consent | `_reveal`, `trade`, `pending`, `incoming` | offer accept/reject and lock probes | A-01 |
| Untraded revealed cards remain active player's | `finish_trading` | transition probe | none |
| 3. Phase: all received/revealed cards must be planted; owner chooses order; forced harvest first | `build`, `plant_incoming` | multi-owner build probe | none |
| 4. Phase: active draws three in order behind hand; next clockwise player | `finish_building`, `_draw` | transition probe | none |
| Die Bohnenernte: harvest any time, Bohnometer payment, paid cards to coin pile, rest discard, field empty | `_harvest`, harvest actions, `METERS` | meter boundary probes | none |
| Bohnenschutzregel: singleton cannot be harvested if any own field has >1 | `_harvestable` | legal-action probe | none |
| Ein leerer Nachziehstapel: shuffle discard as new face-down deck | `_draw` | exhaustion probe | A-02 |
| Spielende: third exhaustion; finish phases 2/3; final fields harvested, hands ignored; most talers; clockwise-from-start tie | `_draw`, `_finalize`, `returns`, `winner_order` | terminal scoring probe | none |
| Variant 1: Kakao-, Weinbrand-, Kaffeebohnen (page 10 reference) | not implemented | Explicitly outside assigned Grundspiel 4–5 condition | none |
| Variant 2: Ackerbohne (4–5), altered meter/third field return (pp.10–11) | not implemented | Explicit variant, outside assigned base condition | none |
| Elsterbohne (page 2 note) | not implemented | Variant-only named component, no supplied gameplay section | none |

The illustrations and examples 1–5 are exercised by the corresponding phase/trade/harvest transitions above; they introduce no additional rule.
