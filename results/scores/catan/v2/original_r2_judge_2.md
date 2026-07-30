## 1. Score

`0.72`, confidence `high`.

The implementation correctly covers most setup, production, trade, build, robber, development-card, privacy, and victory rules. However, Longest Road is entirely absent from state transitions and scoring, and three approved digital decisions are materially violated. No issue appears critical because ordinary games can still advance and terminate, but winner timing and legality can be wrong.

The permitted behavior where a later bank action retrieves a resource just returned to the bank is not penalized.

## 2. Findings

### Major 1 — Longest Road is never calculated or awarded

- Canonical facts: `CAT-C-LR-THRESHOLD`, `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, `CAT-C-LR-VACANT-TIE`.
- Evidence type: `rule_quote`.
- Sources:
  - `CATAN22-RULES`, PDF p.3: “Wer zuerst eine durchgehende Straße aus mindestens 5 Einzelstraßen besitzt …”
  - `CATAN22-RULES`, PDF p.3: “Sobald ein anderer Spieler eine längere Straße besitzt …”
  - `CATAN22-ALMANAC`, PDF p.8: “ist der Besitzer … am Gleichstand beteiligt, so behält er diese.”
  - `CATAN22-ALMANAC`, PDF p.8: if the incumbent is not involved in the leading tie, the card is set aside.
- Conflicting code:
  - `Game.apply_action`, transitions `build_road`, `place_free_road`, and `build_settlement`.
  - `Game._score`.
  - `special_cards.longest_road_owner` and `longest_road_length`.
- Expected: road placement and opponent settlement placement must recompute the approved maximum trail, award or transfer Longest Road at five or more, preserve a tied incumbent, or vacate the award when appropriate. Its two points must immediately affect victory.
- Implemented: the fields initialize to `None` and `0` and are never changed. `_score` consequently never awards Longest Road points.
- Impact: games can miss or delay a legitimate win, and may ultimately report a different winner.

### Major 2 — Road Building ignores the player’s remaining road stock

- Canonical fact: `CAT-C-BUILD-STOCK`.
- Evidence type: `rule_quote`.
- Source: `CATAN22-ALMANAC`, PDF p.6: “Sind keine entsprechenden Figuren mehr im Vorrat, kann nicht gebaut werden.”
- Conflicting code:
  - `Game._road_actions(d, p, free=True)`.
  - `Game.apply_action` transition `place_free_road`.
- Expected: Road Building places at most the feasible number of roads, including the limit imposed by remaining physical road pieces.
- Implemented: the stock check is inside `if not free`, so free-road actions remain legal with zero roads available. Each placement then decrements the stock, allowing negative road supply and extra roads beyond the 15-piece limit.
- Impact: illegal network expansion can change blocking, Longest Road eligibility, and victory.

### Major 3 — Submitted discards are not escrowed against development-card interrupts

- Canonical fact: `CAT-M-DISCARD-ESCROW`.
- Evidence type: `human_decision`.
- Provenance:
  - `CATAN22-V2-CLAIMS`, JSON Pointer `/claims/122`: “The source gives no submitted-card escrow behavior under a development-card interrupt before simultaneous settlement.”
  - `CATAN22-V2-RULEFACTS`, Approved decision 10: “submitted private selections are unavailable to interrupts and settle together after every required submission.”
- Conflicting code:
  - `Game._next_discard`.
  - `Game._dev_actions`.
  - `Game.apply_action` transitions `submit_discard` and `play_monopoly`.
- Expected: after submission, selected cards remain privately escrowed and unavailable to Monopoly or other intervening effects until all discards settle simultaneously.
- Implemented: submitted selections remain in the resource hand until the last player submits. An interrupting Monopoly can transfer those cards away; final settlement then subtracts the stale selection and can create negative resource counts.
- Impact: material state corruption during an approved interrupt sequence.

### Major 4 — Domestic trade offer construction is unbounded

- Canonical fact: `CAT-M-TRADE-OFFER-BOUND`.
- Evidence type: `human_decision`.
- Provenance:
  - `CATAN22-V2-CLAIMS`, JSON Pointer `/claims/121`: “The source gives no finite digital bound for incremental offer construction.”
  - `CATAN22-V2-RULEFACTS`, Approved decisions 5 and 9: finite bilateral offer builder, with give/take totals capped by each side’s public resource-hand size.
- Conflicting code:
  - `Game.legal_actions`, phase `trade_offer`.
  - `Game.apply_action`, transition `add_trade_item`.
- Expected: offer totals are finitely capped by the applicable public hand sizes, while actual holdings are revalidated on acceptance.
- Implemented: `add_trade_item` can increment either bundle without limit. Only acceptance checks actual holdings.
- Impact: the reachable state/action space is unbounded and arbitrarily impossible offers can be proposed, contradicting the approved finite protocol.

### Minor 1 — Played progress cards remain in `development_hand`

- Canonical fact: `CAT-C-PROGRESS-REMOVED`.
- Evidence type: `rule_quote`.
- Source: `CATAN22-RULES`, PDF p.4: “Danach wird die Karte aus dem Spiel entfernt.”
- Code: `Game._play_card` marks the card revealed and adds a play record but does not remove it from `development_hand` or place it in a removed zone.
- Expected: a played progress card leaves the game.
- Implemented: it remains in the player’s hand as an inert revealed card. Current scoring and replay restrictions prevent a major gameplay effect, making this principally a zone/inventory inconsistency.

## 3. Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Beginner setup, 3/4 players | Covered | Illustrated board constants, red removal, pieces, starting resources, robber, bank and deck present |
| Turn order and strict phases | Covered | Seat 0 designated oldest; roll → trade → build; clockwise advancement |
| Production and shortages | Covered | Settlement/city additive production, desert/robber blocking, all-or-none shortage |
| Domestic trade | Partial | Consent and atomic transfer work; offer construction is unbounded |
| Maritime trade | Covered | Harbor ratios, access and different receive type enforced |
| Building legality and costs | Partial | Normal costs, distance, connectivity and city replacement work; free-road stock fails |
| Longest Road | Missing | No route calculation, ownership, tie handling, scoring, or transfer |
| Seven and robber | Partial | Sequence, threshold, discard amount, movement and blind theft work; escrow interrupt fails |
| Development cards | Mostly covered | Timing, one-card limit, effects, deck distribution, Largest Army and interrupts implemented |
| Private information/chance | Covered | Player observations hide resource and development identities; seeded dice/deck/theft |
| Scoring and victory | Partial | Buildings, Largest Army, VP cards, active-player immediate victory work; Longest Road absent |
| Terminal state and returns | Covered | Terminal actions stop; winner receives `1`, others `-1` |
| Serialization | Mostly covered | Full state and player-specific observation are distinct; progress-card zone is inconsistent |

## 4. Missing deterministic scenarios

- A fifth continuous road awards Longest Road and immediately wins if it raises the active player to ten.
- A strictly longer route transfers Longest Road.
- An opponent settlement interrupts a route:
  - incumbent remains in a leading tie;
  - leading tie excludes incumbent and vacates the card;
  - one player becomes the unique qualifying leader.
- Road Building with zero road pieces places none and resumes.
- Road Building with one road piece places exactly one.
- A player submits a discard containing a resource subsequently named by an interrupting Monopoly; escrow prevents transfer and final counts remain nonnegative.
- Trade construction stops when either bundle reaches its approved public hand-size cap.
- Played Road Building, Year of Plenty, and Monopoly cards are absent from the development hand and present only in an out-of-game/public-history representation.

## 5. Material questions for a human

- Confirm whether `state_to_data` is privileged engine state only. If players can access it, it exposes every private resource and development identity despite the otherwise-correct player observation API.
- Confirm whether `development_hand` is intended as an authoritative card zone or merely acquisition history. This determines whether the progress-card retention is a state-integrity issue beyond minor severity.
- No additional rulebook clarification is needed for the four major findings: the printed facts or approved digital decisions resolve them.

```text
score: 0.72
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```