# Rule coverage — assigned 4–5-player Grundspiel

All locations refer to the supplied publisher rulebook. Probes are exercised through `Game.legal_actions` and `Game.apply_action`; `agentic_self_check.py` additionally probes every exposed legal action.

| Source section / named item | Implementing symbol | Source-only probe / status | Assumption |
|---|---|---|---|
| Spielmaterial & Spielvorbereitung (pp.3–4): 104 cards, eight base sorts; 4–5 players use two fields; start player; five individually dealt ordered cards; remaining draw pile | `BEANS`, `Game.__init__`, `Game.initial_state`, `GameState` | Initial-state counts, two fields, five cards, active player 0; seeded shuffle represents mixing | none |
| Card identities/counts: Gartenbohne 6, Rote Bohne 8, Augenbohne 10, Sojabohne 12, Brechbohne 14, Saubohne 16, Feuerbohne 18, Blaue Bohne 20 | `BEANS` | Sum is 104; deck construction uses each printed count | none |
| Variant-only named sorts: Kakaobohne, Weinbrandbohne, Kaffeebohne, Ackerbohne, Elsterbohne | deliberately absent from `BEANS` | Excluded by p.3 note for the assigned base condition | none |
| Hand order cannot change; first dealt is front | `hands`, phase-1 `pop(0)`, phase-4 `append` | Only front card has a phase-1 planting action; trading can select any hand position | none |
| Spielablauf (p.5): clockwise turns, fixed start-player card, four ordered phases | `active`, `phase`, `apply_action` | Phase transitions and `(active+1)%players`; start player remains index 0 | none |
| Wichtige Regeln für den Bohnenanbau: one sort per field; same sort on multiple fields | planting branches in `legal_actions` | Compatible/empty fields only; both compatible fields exposed | none |
| Phase 1: mandatory front card, optional second front card, never third; empty hand skips | `planted_from_hand`, phase-1 actions | End action absent before first planting unless hand empty, present after second | none |
| Forced harvest before an incompatible mandatory planting | global `Ernten` actions plus absence of incompatible planting | Harvest creates the required empty field; protection rule still applies | none |
| Phase 2: reveal top two; revealed cards belong to active player for planting/trading | `_draw`, `exposed` | Reveal action creates up to two public cards | A-02 |
| Regeln für den Bohnenhandel: only active player trades; any hand position; active may trade revealed cards; received/field cards cannot trade; unequal quantities | phase-2 trade generation, `pending` | Partners cannot trade each other; sources are active hand/exposed and partner hand only; pending excluded; one-for-one and sourced 2-for-1 | A-01 |
| Example 1 (Sojabohne offered, Blaue Bohne retained) | `exposed`, `Handel beenden` | Any revealed card can be offered; untraded card remains for phase 3 | A-01 |
| Example 2 (revealed Sojabohne + hand Feuerbohne for hand Rote Bohne) | `Bohnenhandel 2 gegen 1` | Mixed exposed/hand two-for-one source supported | A-01 |
| Consent and do not remove hand card before agreement | atomic trade actions | Mutation happens only when accepted atomic action is applied | A-01 |
| Example 3; acquired cards placed beside fields, never into hand | `pending` | Both sides' receipts enter pending | none |
| Gifts require recipient agreement | `Bohnenkarte schenken` | Atomic accepted gift; no rejected proposal mutates state | A-01 |
| Trading may continue after revealed cards traded; active ends phase voluntarily | phase-2 generation, `Handel beenden` | Hand trades remain after exposed list empties | none |
| Phase 3: all players plant traded cards; active also plants untraded revealed cards; owner chooses order | `pending`, `exposed`, `Neue Bohnenkarte anbauen` | All pending owners processed; currently first owner/card order is deterministic, while field choice remains legal | A-01 (executable protocol) |
| Example 4 and forced harvest during phase 3 | phase-3 planting and global `Ernten` | Pending/revealed cards plant to matching/empty fields; harvest action unlocks incompatible card | none |
| Phase 4: active draws three sequentially behind hand; left player becomes active | phase-4 action, `_draw` | Appends in draw order and advances clockwise | A-02 |
| Die Bohnenernte: harvest any time, including nonactive; printed Bohnometer; zero possible; coin cards removed, remainder discarded, field empty | `BEANS` meters, global harvest actions, `_harvest` | Harvest actions generated for every player; rewards thresholded and field cleared | none |
| Saubohne meter example: 1–2→0, 3–4→1, 5–6→2, 7→3, 8+→4 | `BEANS["Saubohne"]` | Direct threshold transcription | none |
| Example 5: three Feuerbohnen yield one coin and two discards | `BEANS["Feuerbohne"]`, `_harvest` | Direct state probe gives +1 coin, +2 discard, empty field | none |
| Die Bohnenschutzregel: singleton cannot be harvested if another own field has >1 | `_harvestable` | Such singleton action is absent; other fields remain harvestable | none |
| Ein leerer Nachziehstapel: after last card, shuffle discard into new face-down pile | `_draw` | First/second depletion moves and shuffles discard | A-02 |
| Spielende: third depletion; if during phase 2 finish phases 2 and 3; final field harvest; hands ignored; cards in coin pile score; most wins; clockwise-farthest-from-start tie break | `empty_count`, `end_after_phase3`, `_finish`, `returns` | Phase-2 trigger delays; other trigger finishes; all fields harvested; `max(tied)` implements distance from fixed player 0 | none |
| Variante 1: Drei neue Bohnensorten (p.11 first section; heading referenced on p.12), changed phase 4 and 3-player end | not implemented | Outside assigned 4–5-player base condition; supplied page lacks its setup/card list heading content | none |
| Variante 2: Die Ackerbohnen (für 4–5 Spieler): base sorts + Acker-/Weinbrandbohnen, variant-1 flow | not implemented | Explicit optional variant, outside assigned Grundspiel | none |
| Ackerbohnen-Ernte: two grant third field if absent, otherwise nothing; three grant three coins; preserve first/second fields on flip | not implemented | Applies only to excluded optional Ackerbohnen variant | none |
