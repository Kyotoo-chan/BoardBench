score: 0.66  
confidence: high

Rationale: The module implements most setup, production, strict turn order, trade/build costs, robber handling, development cards, privacy, scoring, and immediate victory correctly. Four material defects remain, especially the complete absence of Longest Road transitions and unsafe discard escrow.

## Findings

### Major 1 — Longest Road is never calculated, awarded, interrupted, or transferred

- Canonical facts:
  - `CAT-C-LR-THRESHOLD` (`/claims/57`)
  - `CAT-C-LR-BRANCH` (`/claims/58`)
  - `CAT-C-LR-OPP-BLOCK` (`/claims/59`)
  - `CAT-C-LR-TRANSFER` (`/claims/61`)
  - `CAT-C-LR-HOLDER-TIE` (`/claims/62`)
  - `CAT-C-LR-VACANT-TIE` (`/claims/63`)
- Evidence type: `rule_quote`
- Evidence:
  - `CATAN22-RULES`, PDF p.3: “Wer zuerst eine durchgehende Straße aus mindestens 5 Einzelstraßen besitzt …”
  - `CATAN22-RULES`, PDF p.3: “Abzweigungen zählen nicht.”
  - `CATAN22-RULES`, PDF p.3: “Sobald ein anderer Spieler eine längere Straße besitzt …”
  - `CATAN22-ALMANAC`, PDF p.8: “Wird eine Straße durch eine fremde Siedlung unterbrochen …”
  - `CATAN22-ALMANAC`, PDF p.8: a tied incumbent retains the card; if the incumbent is excluded from the leading tie, the card is set aside.
- Conflicting symbols/transitions: `build_road`, `place_free_road`, `build_settlement`, `special_cards`, `_score`, `_victory`.
- Expected: Road changes and blocking settlements must recompute the approved maximum route, update ownership/ties immediately, apply two points, and check victory.
- Implemented: `longest_road_owner` remains `None` and `longest_road_length` remains `0`; no transition computes either value. Consequently, its two points can never contribute to victory.

### Major 2 — Road Building ignores remaining road-piece stock

- Canonical facts:
  - `CAT-C-BUILD-STOCK` (`/claims/49`)
  - `CAT-C-ROAD-BUILDING` (`/claims/73`)
  - `CAT-M-ROAD-BUILDING-SHORT` (`/claims/94`)
- Evidence type: `rule_quote`
- Evidence: `CATAN22-ALMANAC`, PDF p.6: “Sind keine entsprechenden Figuren mehr im Vorrat, kann nicht gebaut werden.” Also: “2 Straßen bauen, ohne Rohstoffe zu zahlen”.
- Evidence type: `human_decision`
- Evidence: `CATAN22-V2-RULEFACTS`, “Approved decisions” §2: “Road Building places the maximum feasible number up to two.”
- Conflicting symbols/transitions: `_road_actions(d, p, free=True)`, `play_road_building`, `place_free_road`.
- Expected: With zero road pieces, place zero; with one, place at most one; never make stock negative.
- Implemented: The stock check is guarded by `if not free`, so free roads bypass it. A player with zero or one road pieces can place two and reach negative stock.

### Major 3 — Submitted discard escrow remains stealable and monopolizable

- Canonical fact: `CAT-M-DISCARD-ESCROW` (`/claims/122`)
- Evidence type: `human_decision`
- Evidence: `CATAN22-V2-RULEFACTS`, “Approved decisions” §10: “Submitted private selections are unavailable to interrupts and settle together after every required submission.”
- Supporting printed source: `CATAN22-RULES`, PDF p.4: “Alle Spieler … wählen die Hälfte ihrer Rohstoffkarten aus und legen diese zurück.”
- Conflicting symbols/transitions: `submit_discard`, `_next_discard`, `steal_resource`, `play_monopoly`.
- Expected: Submitted cards enter protected escrow. Development interrupts cannot steal or transfer them, and final settlement cannot produce negative holdings.
- Implemented: Submitted selections remain in `players[p]["resources"]` until every player submits. An interrupting Knight or Monopoly can remove them; `_next_discard` later subtracts the original selection anyway, potentially creating negative resources.

### Major 4 — Domestic trade offers have no approved finite bound

- Canonical fact: `CAT-M-TRADE-OFFER-BOUND` (`/claims/121`)
- Evidence type: `human_decision`
- Evidence: `CATAN22-V2-RULEFACTS`, “Approved decisions” §9: “Give/take totals are capped by each side’s public resource-hand size without revealing identities; acceptance validates actual holdings.”
- Supporting printed source: `CATAN22-ALMANAC`, PDF p.6: “Es darf frei ausgehandelt werden, wie viele Rohstoffkarten getauscht werden.”
- Conflicting symbols/transitions: `legal_actions` in `trade_offer`, `add_trade_item`, `propose_domestic_trade`.
- Expected: Each bundle’s total is capped by the relevant player’s public hand size, followed by actual-holdings validation on acceptance.
- Implemented: `add_trade_item` is always available for every direction and resource. Either bundle can grow without limit, creating an unbounded offer-building transition system. Acceptance validation alone does not satisfy the approved construction bound.

### Minor 1 — Played progress cards remain in the development hand

- Canonical fact: `CAT-C-PROGRESS-REMOVED` (`/claims/76`)
- `CATAN22-RULES`, PDF p.4: “Danach wird die Karte aus dem Spiel entfernt.”
- `_play_card` marks the card revealed and adds another record to `bank.played_development`, but leaves the original card in `development_hand`.
- It cannot be replayed, so gameplay impact is localized, but the zone/state representation contradicts removal from the game.

### Question 1 — Should a player observe its own in-progress discard draft?

- Relevant facts: `CAT-M-DISCARD-PROTOCOL`, `CAT-M-DISCARD-ESCROW`.
- `observation_to_data` removes `selected` from every discard frame, including the selecting player’s observation.
- The packet establishes private, simultaneous submission and protected escrow, but does not explicitly define whether an unsubmitted digital draft must appear in the chooser’s observation. A human decision is needed if observations are expected to be self-contained rather than dependent on action history.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Beginner setup, 3/4 players | Covered | Illustrated pieces, resources, colors, bank, deck, robber represented |
| Turn order and strict phases | Covered | Roll → trade → build; clockwise transition |
| Production and shortages | Covered | Settlements/cities, robber blocking, additive claims, all-or-none shortage |
| Domestic/maritime trade | Partial | Ratios and consent work; offer construction is unbounded |
| Building legality and costs | Partial | Normal builds mostly correct; free roads bypass stock |
| Longest Road | Missing | No calculation or ownership transitions |
| Seven, discard, robber | Partial | Main sequence works; submitted escrow is unsafe under interrupts |
| Development cards/Largest Army | Mostly covered | Effects and timing represented; progress-card zone is inaccurate |
| Private information | Mostly covered | Resource/development identities hidden; discard-draft visibility undecided |
| Scoring and terminal state | Partial | Immediate active-player victory works, but Longest Road points are absent |
| Returns | Covered | Winner receives `1`, others `-1`; nonterminal returns zero |

## Missing deterministic scenarios

- Fifth continuous road immediately awards Longest Road and two points.
- A strictly longer road transfers Longest Road and triggers immediate victory if applicable.
- Opponent settlement interruption: incumbent-leading tie, incumbent-excluded tie, and unique new leader.
- Road Building with zero and exactly one road piece remaining.
- Road Building’s first free road awards Longest Road and immediately ends the game before the second placement.
- Multiple seven discards followed by interrupting Monopoly and Knight; escrowed cards remain unavailable and no count becomes negative.
- Domestic offer construction at each public hand-size bound, including overlapping resource types in give/take bundles.
- Played Road Building, Year of Plenty, and Monopoly cards leave the development hand and enter a removed/public-history zone.
- If clarified, observation of a player’s own partially selected discard and undo actions.

## Material questions for a human

- Must the selecting player’s observation expose its current, unsubmitted discard draft? The supplied packet does not explicitly decide that digital observation detail.

```text
score: 0.66
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```