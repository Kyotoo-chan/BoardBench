## 1. Score

`score: 0.43` — `confidence: high`

The module models the basic four-phase loop, correct 129-card inventory, ordered-hand planting, field protection, Ackerbohne rewards, final harvesting, and tiebreak correctly. However, seven material deviations affect scoring, trading, private information, harvest availability, planting choice, and deck exhaustion. None appears likely to prevent the game from completing altogether, so I found no critical issue.

## 2. Findings

### Major 1 — Weinbrandbohne harvest values are wrong

- Canonical fact: `GOLD-09`
- Evidence type: `user_observation`
- Source: `COMPONENTS`, JSON Pointer `/bohnen/9/ernte`
- Exact evidence: `[{"ab_bohnen":4,"gold":1},{"ab_bohnen":7,"gold":2},{"ab_bohnen":9,"gold":3},{"ab_bohnen":11,"gold":4}]`
- Conflicting symbol: `BOHNOMETER["Weinbrandbohne"]`
- Expected: 0 below four cards; then 1/2/3/4 coins at 4/7/9/11+.
- Implemented: 1/2/3/4 coins at 2/4/6/8+.

This substantially overpays a 22-card bean type and can change the winner.

### Major 2 — Depletion is detected one draw attempt too late

- Canonical facts: `DECK-01`, `END-01`, `END-05`
- Evidence type: `human_decision` applying the printed depletion rule
- Source: `RULES`, PDF page 9
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels. Lege sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.” Also: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting symbol/transition: `Game._take_card`; `draw_one → next actor`
- Expected: depletion occurs when the last card is drawn. First/second depletion immediately reshuffles the then-current discard; third depletion during phase 4 terminates after that draw and before another player acts.
- Implemented: `empty_count` changes only when `_take_card` begins with an already-empty deck. Drawing the last card neither reshuffles nor triggers the end. A later draw action discovers the emptiness.

Consequences include allowing intervening harvest discards into a reshuffle they should have missed and exposing an extra phase-4 draw action after the terminal depletion.

### Major 3 — Off-turn harvesting is unavailable to most owners

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting symbol: `Game.legal_actions`
- Expected: any owner may harvest between atomic game steps, including during another player’s turn.
- Implemented: harvest actions are generated only for `p = s.actor`. Non-acting owners normally have no way to harvest; a trade recipient gets an incidental opportunity only while responding.

This removes a material timing option from inactive players.

### Major 4 — Unequal multi-card trades cannot be proposed atomically

- Canonical fact: `TRADE-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
- Conflicting symbols: `offer_trade`, `offer_gift`, `accept_offer`
- Expected: an atomic consensual exchange may contain different nonzero quantities, such as two cards for one.
- Implemented: proposals are restricted to one active-player card for either zero cards (`offer_gift`) or one target card (`offer_trade`).

Several sequential 1:1 or gift actions are not equivalent because each transfer is separately accepted and received cards cannot legally be reused.

### Major 5 — The active player can retrade a received card

- Canonical fact: `TRADE-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Mit Karten, die ihr nach einem Handel bekommt, dürft ihr nicht weiterhandeln.”
- Conflicting symbols: `accept_offer`; table-source construction in `legal_actions`
- Expected: a received card waits beside its owner’s fields and cannot be traded again.
- Implemented: a card received by the active player is appended as `[s.active, wanted]`. All table entries owned by the active player are subsequently included as trade sources, without distinguishing retained reveals from received cards.

### Major 6 — Phase-3 planting order is fixed rather than chosen

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting symbol: `legal_actions`, `plant_table` stage
- Expected: each recipient chooses which received/retained card to plant next, including before deciding any necessary harvest.
- Implemented: only `owned[0]` can be planted. No action selects another owned table card.

This can force a different harvest and field outcome from a legal chosen ordering.

### Major 7 — Private hands are exposed through actions, with no compliant observer view

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar. Jede weitere steckst du dahinter.” The approved convention specifies that the owner sees their complete ordered hand while opponents see only its count unless voluntarily communicated.
- Conflicting symbols: `GameState.hands`, `Game.legal_actions`, `Game.render`
- Expected: a player-specific observation shows the viewer’s ordered hand and only opponents’ counts.
- Implemented:
  - Raw state contains every hand.
  - Active-player trade actions enumerate every target hand position and bean name.
  - `render` hides all hand identities, including the viewer’s own, and has no viewer parameter.

This is adjudication-dependent rather than a contradiction of unambiguous printed visibility language, but it directly violates the approved executable privacy convention.

### Minor 1 — Empty-hand phase 1 requires two skip transitions

- Canonical fact: `P1-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.”
- Conflicting transition: `advance_plant`
- Expected: an empty hand at the start proceeds directly to reveal.
- Implemented: `plant_first → plant_second → reveal`, requiring two `advance_plant` actions and creating an extra harvest decision boundary.

## 3. Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and inventory | Pass | 4–5 players, two initial fields, five cards, and 129-card selected deck |
| Ordered hand | Partial | Front planting/removal preserve order; observer privacy is noncompliant |
| Turn and phase order | Mostly pass | Four phases and clockwise active player; empty-hand skip has an extra step |
| Phase-1 planting | Pass | Mandatory first, optional second, no third |
| Reveal | Pass | Two public cards, subject to depletion-timing defect |
| Trading | Fail | No unequal bundles; received active-player cards can be retraded; hidden hands leak |
| Mandatory planting | Fail | All cards are planted, but their order is forced |
| Phase-4 draw | Partial | One per player clockwise; exhaustion timing is wrong |
| Ordinary harvesting | Partial | Protection and payout mechanics mostly correct; off-turn access is absent |
| Ackerbohne | Pass | One/two/three-card outcomes and third-field persistence match approved facts |
| Terminal conditions | Partial | Third depletion eventually ends play, but at the wrong transition |
| Final scoring/returns | Partial | Final harvest and tiebreak work; Weinbrand scoring can produce the wrong winner |
| Chance | Partial | Seeded shuffle exists; delayed reshuffling changes eligible discard contents |

## 4. Deterministic scenarios needed

- Weinbrand harvests at 2, 4, 6, 7, 8, 9, 10, and 11 cards.
- First/second depletion caused by drawing the last card, verifying immediate discard capture.
- Third depletion on a phase-4 draw, verifying no subsequent player action.
- Phase-2 depletion with exactly one and exactly two cards remaining.
- Atomic 2-for-1 trade acceptance and rejection.
- Active player receives a card, then attempts to offer that received card again.
- Phase-3 ownership of two different beans where planting order changes the necessary harvest.
- An inactive player harvesting between each type of atomic step.
- Player-specific observations and trade-action lists with unrevealed opponent hands.
- Empty hand at the start of phase 1 proceeding directly to reveal.
- Full terminal scoring with Weinbrand, Ackerbohne, and a tied coin total.

## 5. Material questions for a human

- What method is intended to provide player-specific observations? No compliant observer API is present.
- Is fixed seat 0 an accepted representation of the configured start player, or must callers be able to select another starting seat?
- Must chance be exposed as explicit chance actions, or is internally seeded shuffling an accepted interface convention?

These are integration questions; the supplied rule condition does not require further rulebook clarification.

```text
score: 0.43
confidence: high
critical_issues: 0
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```