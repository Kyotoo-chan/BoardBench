score: 0.56  
confidence: high

The module captures the selected 4–5-player Ackerbohne variant’s inventory, ordered hands, phase structure, harvesting rewards, reshuffling, final scoring, and tie-break correctly. However, four material contradictions affect action authority, private information, trading, and termination.

## Findings

### Major — Any acting player can harvest an opponent’s field

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting symbols: `Game.legal_actions`, `Game.current_player`, `Game.apply_action`
- Expected: A field’s owner may choose to harvest it between atomic steps.
- Implemented: `legal_actions` emits `Action("harvest", (p, i))` for every player’s fields, regardless of `state.actor`. The current actor can therefore submit a harvest for an opponent, including during offer response or another player’s planting.
- Impact: Opponents can empty or alter another player’s fields without that owner’s decision, materially affecting planting and scoring.

### Major — Player-private hands are exposed

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar. Jede weitere steckt sich dahinter.”
- Approved decision: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
- Conflicting symbol: `Game.render`
- Expected: A player-specific observation contains that player’s ordered hand and only opponents’ hand counts.
- Implemented: `render` serializes `[list(h) for h in s.hands]`, exposing every ordered hand to every viewer. It accepts no viewing-player argument and offers no alternative private observation method.
- Impact: Hidden information central to negotiation and hand-order planning is removed. This is adjudication-dependent rather than a contradiction of an express printed secrecy sentence.

### Major — The trade action space cannot express all permitted gifts or card choices

- Canonical facts: `TRADE-02`, `TRADE-07`
- Evidence type: `rule_quote`
- Sources:
  - `RULES`, PDF page 5: “Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
  - `RULES`, PDF page 6: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Conflicting symbols: `Game.legal_actions`, `add_give`, `add_ask`, `propose_offer`, `accept_offer`
- Expected:
  - Either side of a trade involving the active player can give a nonempty consensual gift.
  - A player can select a card from any hand position.
  - The active player can distinguish a revealed card from an identically typed hand card.
- Implemented:
  - `propose_offer` is legal only when `offer_give` is nonempty, so the inactive player cannot gift cards to the active player without receiving something.
  - Offers identify cards only by bean name. `_remove_multiset` always removes the first matching hand occurrence.
  - `accept_offer` consumes an identically typed face-up card before an active-player hand card, with no action to select the source.
- Impact: Legal negotiations are absent, and the forced source choice can change both the active player’s remaining ordered hand and which revealed cards must be planted.

### Major — Third depletion during reveal does not terminate immediately after phase 3

- Canonical fact: `END-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
- Conflicting transitions: `finish_hand_planting` → `finish_received` → `draw_round` → `draw_one`
- Expected: When the third depletion happens during phase 2, finish trading and mandatory planting, skip phase 4, and score immediately.
- Implemented: Because revealed cards exist, `finish_hand_planting` does not finish the game. After phase 3, `finish_received` enters `draw_round`; the game becomes terminal only after an additional `draw_one` action observes `empty_count >= 3`.
- Impact: Phase 4 is observably entered, termination requires an extra action, and harvest actions remain available in the intervening state.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and inventory | Pass | 4–5 players, two initial fields, five cards each, and the 129-card deck are represented. |
| Start player and turn order | Pass/assumption | Seat 0 is permanently treated as the designated start player; clockwise order is correct. |
| Ordered hand planting | Pass | Mandatory first card, optional second, no third, and append-only draws are implemented. |
| Reveal and trading | Major gap | Basic bilateral consent works, but gifts and card/source selection are incomplete. |
| Mandatory planting | Pass | Received and retained face-up cards must be planted in selectable order. |
| Drawing and reshuffling | Pass | Each player draws one; first/second depletion reshuffles discard before continuing. |
| Harvesting and protection | Major gap | Rewards and protection are correct, but harvest ownership is unenforced. |
| Ackerbohne | Pass | One, two, and three-card harvest outcomes match the approved decisions. |
| Private/public information | Major gap | All ordered hands are exposed. |
| Terminal conditions | Major gap | Phase-2 third depletion terminates one action too late. |
| Returns and tie-break | Pass | Coins remain observable; winner and clockwise-distance tie-break are correct for start seat 0. |
| Unsupported components/elimination | Pass | Excluded bean types are absent; no elimination mechanism is introduced. |

## Missing deterministic scenarios

- An actor attempts to harvest every other player’s field; only owner-authorized harvests should be legal.
- Render observations for each seat with distinct ordered hands; opponents should expose counts only.
- An inactive player gives a one-way consensual gift to the active player.
- Active player trades a hand card while retaining an identically typed face-up card.
- A hand such as `A, B, A` trades specifically the later `A`, preserving `A, B`.
- Third deck depletion on the first and second reveal respectively; phases 2–3 should finish and terminal scoring should follow without a `draw_one`.
- First/second depletion during a two-card reveal with a populated discard pile; the remaining reveal should come from the reshuffled pile.
- Third depletion on each seat’s phase-4 draw; no later seat should draw.
- Final harvest containing one, two, and three Ackerbohnen, both with and without an already unlocked third field.
- Tied coin totals for every possible tied-seat subset at four and five players.

## Material questions for a human

- Is seat 0 guaranteed by the integration contract to be the already chosen start player? If not, the constructor needs a start-player parameter. This was not scored because player relabelling can validly designate seat 0.
- Is `render` the official player observation API, or is an unprovided wrapper expected to redact hands and expose pending offer terms? The submitted module itself provides no such wrapper.
- Is a harvest action carrying `(owner, field)` assumed to arrive through an external owner-authorization layer? No such enforcement is present in the reviewed implementation.

```text
score: 0.56
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```