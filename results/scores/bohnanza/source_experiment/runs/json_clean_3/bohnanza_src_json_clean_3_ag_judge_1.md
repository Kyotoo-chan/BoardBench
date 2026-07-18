## Review outcome

`score: 0.48`, `confidence: high`.

The module gets inventory, ordinary planting, harvest yields, Ackerbohne rewards, clockwise turns, and winner calculation largely right. Material defects remain in trade expressiveness, harvest ownership, private information, and the phase-2 terminal transition. None appears to make normal play universally impossible, so I found no critical issue.

## Findings

### Major 1 — Other players’ fields can be harvested by the current actor

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting symbols: `Game.legal_actions`, `Game.current_player`, `Game.apply_action`
- Expected: A field’s owner decides whether to harvest it between atomic steps.
- Implemented: `legal_actions` offers `Action("harvest", (p, i))` for every player’s harvestable fields to the single current `actor`. That actor can therefore order another player’s harvest. There is no interrupt or ownership-confirmation transition.

This is adjudication-dependent because the approved fact defines the executable timing/ownership convention, but it materially changes player agency.

### Major 2 — The active player cannot receive a one-way gift

- Canonical fact: `TRADE-07`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 6
- Exact evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Conflicting transition: `legal_actions` in phase `trade`, specifically `if s.offer_give: a.append(Action("propose_offer"))`
- Expected: A nonempty one-way gift is legal with the recipient’s consent, including a partner giving cards to the active player.
- Implemented: An offer can be proposed only if `offer_give`—cards moving from the active player—is nonempty. An offer with empty `offer_give` and nonempty `offer_ask` cannot be proposed.

### Major 3 — Trades cannot identify which hand occurrence is transferred

- Canonical fact: `TRADE-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
- Conflicting symbols: `add_give`, `add_ask`, `_remove_multiset`
- Expected: A player can trade a card from any chosen hand position while the remaining cards preserve their order.
- Implemented: Offers record only bean names. `_remove_multiset` uses `list.remove`, which always removes the first matching occurrence. With the same bean at multiple separated positions, the player cannot select which occurrence leaves the hand, and the resulting front/order can differ materially.

### Major 4 — Face-up and hand copies of the same bean cannot be distinguished

- Canonical fact: `TRADE-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Als aktiver Spieler darfst du auch mit den zwei aufgedeckten Karten handeln.”
- Conflicting symbols: `add_give`, `accept_offer`
- Expected: The active player chooses whether a traded bean comes from their hand or from the public face-up cards.
- Implemented: Offers identify only the bean type. On acceptance, `accept_offer` always consumes matching `face_up` copies before hand copies. A legal choice to trade the hand copy while retaining the face-up copy is unavailable.

### Major 5 — Third depletion during reveal ends one action too late

- Canonical fact: `END-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
- Conflicting transitions: `finish_hand_planting` → `plant_received` → `finish_received` → `draw_round`
- Expected: After third depletion during phase 2, complete trading and mandatory planting, skip phase 4, and score immediately.
- Implemented: After phase 3, `finish_received` enters `draw_round`. The game becomes terminal only after the active player submits an artificial `draw_one` action against the already-empty deck.

The eventual score is generally preserved, but the prescribed phase and terminal boundary are materially wrong.

### Major 6 — No private per-player observation is implemented

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar. Jede weitere steckst du dahinter.”
- Approved expectation: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
- Conflicting symbol: `Game.render`; no alternative observation method exists
- Expected: A player-specific observation exposes the viewer’s ordered hand and only opponents’ hand counts.
- Implemented: `render` serializes every player’s complete ordered hand. The module provides no viewer parameter or masking interface.

This finding depends on the approved human privacy decision. If `render` is strictly privileged debugging output and an external masked observation layer exists, a human should confirm that integration contract.

### Minor findings

None.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count and inventory | Pass | 4–5 players; correct 129-card, ten-type deck |
| Initial hands and fields | Pass | Five cards dealt singly; two initial fields |
| Start player | Pass with assumption | Fixed player 0 can represent the chosen player through seat labelling |
| Phase-1 planting | Pass | First mandatory, second optional, no third |
| Field compatibility | Pass | One bean type per field |
| Reveal and trading | Major issues | Gift direction and card-source/position selection |
| Mandatory phase-3 planting | Pass | All retained/received cards planted in chosen type order |
| Variant phase-4 draws | Pass | One card each, active player first clockwise |
| Reshuffling | Pass | First/second depletion continues owed draws when discard exists |
| Harvest protection and yields | Pass | Printed thresholds and singleton protection represented |
| Ackerbohne | Pass | One/two/three-card outcomes and third-field persistence represented |
| Harvest agency | Major issue | Current actor controls every player’s harvest actions |
| Private information | Major issue | Complete hands exposed without player masking |
| End conditions | Major issue | Phase-2 depletion requires an extra phase-4 action |
| Final scoring and tie-break | Pass | Final harvest, hands ignored, farthest clockwise tied seat wins |
| Returns | Pass | Zero nonterminal and winner-based terminal returns |

## Missing deterministic scenarios

Recommended deterministic coverage:

1. Third depletion on the first and second phase-2 reveal, asserting immediate terminal scoring after phase 3 without `draw_one`.
2. Third depletion during phase 4, asserting no remaining players draw.
3. Partner gives a one-way gift to the active player.
4. Trading one of two identical beans from separated hand positions, checking the surviving order.
5. Active player chooses between identical hand and face-up copies.
6. During another player’s turn, only a field’s owner can authorize its harvest.
7. Per-viewer observations: own ordered hand visible, opponents reduced to counts.
8. First/second depletion on the first of two owed reveals, continuing the second reveal after reshuffle.
9. Ackerbohne harvests of one, two with/without field 3, and exactly three.
10. Final tied scores with each possible original start-player-relative seat.

## Material questions for a human

- Is `render` externally visible to players, or is there an external player-specific masking layer not represented in this module? The module itself does not satisfy the approved observation convention.
- Does the host framework treat `current_player()` as the sole decision-maker? If so, the all-player harvest actions definitively give the current actor unauthorized control.

```text
score: 0.48
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```