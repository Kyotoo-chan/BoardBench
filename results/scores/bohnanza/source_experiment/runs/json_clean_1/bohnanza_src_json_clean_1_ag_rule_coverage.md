# Rule coverage — 4–5-player Ackerbohnen condition

The executable condition uses four players (the minimum supported by Variant 2). `Game(seed)` makes shuffling reproducible while keeping deck order out of `render`.

| Source | Rule / named bean | Implementation | Probe / assumption |
|---|---|---|---|
| p2 Spielmaterial & Vorbereitung | 4–5 players use two fields; start-player card; five cards; deck/discard | `initial_state`, `GameState` | setup state inspection; A-01 for start method |
| p2 card list | Gartenbohne 6, Rote 8, Augen 10, Soja 12, Brech 14, Sau 16, Feuer 18, Blaue 20 | `BASE` | constants/source-only count probe |
| p3 hand order | deal singly; front card fixed; never reorder; draw behind | `initial_state`, `plant_hand`, `draw_three` | ordered tuple transition probe |
| p4 Spielablauf | clockwise turns; four phases; start card stays | phase transitions, `active` | rollout probe |
| p4 Bohnenanbau | one type per field; same type may occupy multiple fields; stack cards | `_plant_slots`, planting actions | legal-action probe |
| p4–5 phase 1 | mandatory front card, optional second; harvest first if necessary; empty-hand shortcut | `legal_actions`, `plant_hand`, `skip_second`, `advance` | rollout probe |
| p5 phase 2 | reveal top two; active owns them; use for planting/trading | `_reveal`, `face_up` | state transition probe |
| p5–6 trade rules | only active trades; hands plus active face-up; no field cards; acquired cards not retraded/not put in hand; unequal quantities; gifts require consent | `trade`, `gift`, `gift_to_active`, `pending` | atomic trade probe; bundle limitation A-02 |
| p7 phase 3 | all traded/face-up cards mandatory; each player chooses order | `plant_pending`, `done_planting` | legal-action probe |
| p7 phase 4 | active draws three in order; next player clockwise | `draw_three` | transition probe |
| p7–8 Die Bohnenernte | harvest any time, even inactive; Bohnometer; coin cards to score pile, remainder discard; harvested field empty | harvest actions, `_harvest`, `PAY` | legal and scoring probes (inactive harvest during another actor's decision is not represented) |
| p8 Saubohne example | 3/5/7/8 → 1/2/3/4 | `PAY["Saubohne"]` | constant probe |
| p8 Bohnenschutzregel | singleton protected if any field has multiple cards | `_harvestable` | legal-action probe |
| p9 empty deck | shuffle discard into new face-down deck | `_draw_one` | exhaustion rollout probe |
| p9 Spielende | third empty deck; finish phases 2+3; harvest fields; hands ignored; most coins; clockwise tie break | `ending`, `_draw_one`, `_finish`, `returns` | terminal transition and scoring probe |
| p10 Variante 1 | three-new-bean variant and its two-player rules | not in assigned Variant 2 condition | audited, out of condition |
| p10 Variante 2 | for 4–5; base + Ackerbohne + Weinbrandbohne; two fields; otherwise Variant 1 flow | `EXTRA`, `initial_state` | deck composition probe |
| p11 Ackerbohne | exactly 2 grants third field (no reward if already owned); harvested Acker discarded; later cards return to correct first/second field; exactly 3 gives 3 coins; two gives nothing if third already owned | `_harvest` | branch probes; fields retain stable order |
| observed components | Weinbrandbohne 22, thresholds 4/7/9/11; Ackerbohne 3; all base counts/Bohnometers | `BASE`, `EXTRA`, `PAY` | constants probe; no conflict with publisher images |
| observed-only excluded beans | Kaffeebohne, Kakaobohne | omitted from assigned deck | source-only audit: p2 note and p10 variant composition |
| observed-only named omissions | Elsterbohne, Auftragskarten, AMIGO-Bohnentaler | no implementation | component file says not contained; no gameplay evidence |

Known fidelity boundary: the source permits inactive players to harvest “at any time”; the turn-oriented API exposes harvests to the current decision-maker, including each recipient during phase 3, but cannot interrupt another player's atomic action. This is a material legal-action limitation recorded here because it follows from API serialization rather than a choice between source alternatives.
