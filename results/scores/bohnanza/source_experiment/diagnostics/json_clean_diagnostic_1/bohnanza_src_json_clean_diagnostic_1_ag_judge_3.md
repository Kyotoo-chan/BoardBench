## Review result

`score: 0.42` — `confidence: high`

The module implements the central four-phase loop, ordered hands, planting constraints, harvest yields, Ackerbohne rewards, and basic scoring coherently. However, it omits five-player setup, gives the current actor control over other players’ harvests and trade decisions, supports only a narrow subset of legal trades, exposes private hands, and detects the decisive third depletion too late. The last issue can permit an extra planting phase and alter the winner.

## Findings

### Major

1. **Third deck depletion is detected after the pile is already empty**

- Canonical facts: `END-01`, `END-02`, `END-05`
- Evidence type: `rule_quote` for `END-01`/`END-02`; `human_decision` for `END-05`
- Source: `RULES`, PDF page 9
- Exact evidence:
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
  - Approved `END-05`: third depletion during phase 4 is terminal immediately after the draw that empties the pile, before another player draws.
- Conflicting symbols: `Game._draw`, `Game.apply_action` branch `draw_one`
- Expected: Depletion is recorded when a draw removes the last card. On third depletion in phase 4, finish immediately; in phase 2, finish phases 2–3 and skip phase 4.
- Implemented: `empty_count` increments only when a later draw begins with `deck` already empty. If the last player’s phase-4 draw removes the last card, the game starts another turn and can allow phase-1 planting before detecting the third depletion in phase 2. This can change final harvest values and the winner.

2. **The current actor can harvest any player’s fields**

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.” Approved expectation: “Owner may harvest between individual game steps.”
- Conflicting symbols: `Game.legal_actions`, `Game.current_player`, `Game.apply_action("harvest", hp, i)`
- Expected: A field owner decides whether to harvest their own field, including during another player’s turn.
- Implemented: `current_player()` returns only `s.actor`, but `legal_actions()` offers that actor harvest actions for every `hp`. The active/phase actor can therefore harvest opponents’ fields without their choice.

3. **Trades and gifts do not require the other player’s acceptance**

- Canonical facts: `TRADE-05`, `TRADE-07`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 6
- Exact evidence:
  - “Beide Spieler müssen dem Handel zustimmen.”
  - “Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Conflicting transitions: `give_table`, `trade_table_for_hand`, `trade_hands`
- Expected: A proposal remains pending until both affected players consent; rejection leaves all cards in place.
- Implemented: The active actor directly removes cards from another player’s hand or gives them a card. There is no proposal, accept, or reject state, even though the approved executable conventions explicitly require those choices.

4. **Material legal trade combinations and gifts are absent**

- Canonical facts: `TRADE-02`, `TRADE-04`, `TRADE-07`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 5–6
- Exact evidence:
  - “Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
  - “Ihr dürft euch auch Bohnenkarten schenken.”
- Conflicting symbol: `Game.legal_actions` in phase `trade`
- Expected: The active player and one partner can exchange unequal nonempty quantities, use eligible cards from arbitrary hand positions, or make a consensual nonempty gift.
- Implemented: Exchanges are only one table card for one hand card or one hand card for one hand card. The only gift is a revealed table card from the active player to another player. Hand-card gifts, gifts to the active player, and unequal exchanges such as two-for-one are unavailable.

5. **Private ordered hands are exposed to all controllers**

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.” Approved expectation: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
- Conflicting symbols: public `GameState.hands`; module declaration that “The public state contains hands for inspectability”; absence of a player-specific observation method
- Expected: A player-specific observation exposes the observer’s ordered hand and only opponent hand counts.
- Implemented: Every complete hand is stored in the declared public state without an observation boundary. `render()` hides identities, but direct state access does not.

6. **The approved five-player setup is unsupported**

- Canonical facts: `SET-01`, `SET-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 2 and 10
- Exact evidence:
  - “GRUNDSPIEL (3–5 SPIELER)”
  - “Variante 2: Die Ackerbohnen (für 4–5 Spieler)”
  - “Spielt ihr zu viert oder zu fünft, legt jeder die Seite mit den zwei Bohnenfeldern vor sich ab.”
- Conflicting symbols: `Game.initial_state`, `n = 4`; `GameState.players = 4`
- Expected: The selected Ackerbohne condition supports either four or five configured players, each beginning with five cards and two fields.
- Implemented: `initial_state()` unconditionally constructs four hands, field sets, and coin entries; there is no five-player setup path.

### Minor

7. **Every new game and reshuffle uses the same fixed permutation**

- Canonical fact: `HAND-01` setup context
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 3
- Exact evidence: “Mischt alle Karten und verteilt an jeden Spieler einzeln fünf Handkarten.”
- Conflicting symbols: `random.Random(0).shuffle(deck)` and `random.Random(s.empty_count).shuffle(s.deck)`
- Expected: Shuffling supplies the game’s chance variation, normally through an external or configurable random source.
- Implemented: Every initial game and depletion-number reshuffle repeats the same permutation. This is localized if deterministic replay was intended, but the seed cannot be varied or injected.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Inventory | Pass | Correct 129-card deck and ten selected types |
| Setup | Partial | Correct four-player deal; no five-player configuration |
| Hand order | Pass | Front planting and append-only draws are correct |
| Phase 1 planting | Pass | Mandatory first, optional second, no third |
| Reveal | Pass | Attempts two public draws |
| Trading | Fail | No consent protocol; unequal trades and most gifts absent |
| Mandatory planting | Pass | Received/retained cards remain outside hands and are planted in chosen order |
| Phase 4 draw | Partial | Correct one-per-player order until depletion handling fails |
| Harvest yields | Pass | Printed thresholds and Ackerbohne cases match approved facts |
| Harvest authority | Fail | Current actor can harvest opponents’ fields |
| Private information | Fail | Complete public hands lack player-specific observations |
| Terminal/scoring | Partial | Final harvest and tie-break work for start player 0; depletion timing is wrong |
| Returns | Pass | Nonterminal zero and winner-based terminal returns are permitted |

## Missing deterministic scenarios

- Five-player setup: 129 cards, five cards each, two fields each, and five clockwise phase-4 draws.
- Player-specific observations showing own ordered hand and only opponent counts.
- Inactive owner harvest during another player’s turn, plus rejection of attempts by the actor to harvest that owner’s field.
- Trade proposal rejection with no state mutation.
- Accepted two-for-one exchange using arbitrary hand positions.
- Consensual hand-card gifts in both directions between the active player and a partner.
- Prevention of re-trading received cards.
- Third depletion caused by the last player’s phase-4 draw: immediate scoring with no next phase 1.
- Third depletion during the second reveal: complete phases 2–3 and never enter phase 4.
- Configurable shuffle seed demonstrating reproducibility under one seed and different valid deals under another.

## Material questions for a human

- Is this module intentionally scoped to a four-player subcondition despite the approved condition covering both four and five players? If so, that narrower scope should be explicit in the assigned condition.
- Is `GameState` guaranteed to be inaccessible to player agents, with privacy enforced by an unprovided framework layer? The module itself describes it as public, so no such boundary is currently evident.
- Is the fixed random seed a required replay convention? If yes, the seed should still be injectable so the game’s chance distribution can be exercised.

score: 0.42
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true