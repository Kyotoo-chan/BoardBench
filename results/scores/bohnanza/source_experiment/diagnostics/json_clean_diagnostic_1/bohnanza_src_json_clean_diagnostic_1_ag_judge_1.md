score: 0.42  
confidence: high

The module implements the correct 129-card inventory, ordered hands, core planting sequence, harvest values, Ackerbohne rewards, field protection, and final tie-break for its fixed seat-zero/four-player setup. However, third-depletion timing can materially change the final score, and several required player-authority, trading, setup, and information rules are missing.

## Findings

### Critical

1. Third deck depletion is detected one draw too late and terminal transitions are incorrect.

   - Canonical facts: `END-01`, `END-02`, `END-05`
   - Evidence:
     - `rule_quote`; source `RULES`, PDF page 9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - `rule_quote`; source `RULES`, PDF page 9: “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
     - `human_decision`; source `RULES`, PDF page 9, underlying “endet, sobald”; approved decision: third depletion in variant phase 4 is terminal immediately after the draw that empties the pile, before another player draws.
   - Conflicting symbols/transitions: `Game._draw`, `flip_two`, `draw_one`, and the `draw_left` transition.
   - Expected: Taking the last card creates a depletion immediately. A third depletion during reveal finishes phases 2–3 and skips phase 4; one during phase 4 terminates immediately after that draw.
   - Implemented: `_draw` increments `empty_count` only when a later draw begins with an already-empty deck. During phase 2 the game subsequently enters phase 4; during phase 4 it continues offering draw actions to later players. If the fourth player takes the last card, another turn can begin before depletion is recognized, allowing additional planting and potentially changing coins and the winner.

### Major

2. The complete supported setup is unavailable, and start-player configuration is hard-coded.

   - Canonical facts: `SET-01`, `SET-03`, `END-04`
   - Evidence:
     - `rule_quote`; source `RULES`, PDF page 10: “VARIANTE 2: DIE ACKERBOHNEN (FÜR 4–5 SPIELER)”.
     - `rule_quote`; source `RULES`, PDF page 2: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
     - `rule_quote`; source `RULES`, PDF page 9: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
   - Conflicting symbols: `Game.initial_state` sets `n = 4`; `active` defaults to zero; `returns` assumes player zero was the start player and chooses `max(winners)`.
   - Expected: Both four- and five-player Ackerbohne games can be configured, with a chosen start player retained for turn order and tie-breaking.
   - Implemented: Only a four-player, seat-zero-start game can be created. Five-player setup and a nonzero start player cannot be represented.

3. Trades and gifts execute without the other player's explicit consent.

   - Canonical facts: `TRADE-05`, `TRADE-07`
   - Evidence:
     - `rule_quote`; source `RULES`, PDF page 6: “Denn beide Spieler müssen dem Handel zustimmen.”
     - `rule_quote`; source `RULES`, PDF page 6: “Der beschenkte Mitspieler muss dem Geschenk aber zustimmen. Lehnt er ab, kommt der Handel nicht zustande.”
   - Conflicting symbols/transitions: `give_table`, `trade_table_for_hand`, and `trade_hands` mutate hands/table/traded areas immediately; no proposal, accept, or reject state/action exists.
   - Expected: Cards stay in place until both players accept; rejected proposals and gifts transfer nothing.
   - Implemented: The active actor unilaterally completes every exchange or gift.

4. Required unequal exchanges and general gifts are absent.

   - Canonical facts: `TRADE-04`, `TRADE-07`
   - Evidence:
     - `rule_quote`; source `RULES`, PDF page 5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
     - `rule_quote`; source `RULES`, PDF page 6: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken.”
   - Conflicting symbols: trade action generation in `legal_actions`, particularly `give_table`, `trade_table_for_hand`, and `trade_hands`.
   - Expected: A consensual atomic trade may exchange different nonzero quantities, and legal cards may be offered as gifts.
   - Implemented: Exchanges are only one table card for one hand card or one hand card for one hand card. The only gift is one revealed table card. A two-for-one exchange or a gift from an active player's hand cannot be expressed. Multiple one-for-one actions are not equivalent because each is immediately committed separately.

5. The current actor can harvest another player's fields.

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7.
   - Exact source evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Approved decision: “Owner may harvest between individual game steps, including during another turn.”
   - Conflicting symbols: `current_player` returns `s.actor`, while `legal_actions` adds `("harvest", hp, i)` for every player and `apply_action` performs it without checking ownership.
   - Expected: An inactive owner may choose to harvest their own field; the acting player cannot make that choice for them.
   - Implemented: Whoever controls the current action can harvest any eligible field belonging to any player. This finding depends on the packet’s approved action-authority decision, not merely the printed timing language.

6. Private hands are exposed in the public state without an observation boundary.

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3.
   - Exact approved evidence: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
   - Conflicting symbols: public `GameState.hands`, the module declaration that “The public state contains hands for inspectability,” and the absence of a player-specific observation method.
   - Expected: Each player observes their own ordered hand and only opponents’ hand counts.
   - Implemented: Any consumer receiving the public state can inspect every ordered hand. Restricting who may select a card does not preserve private information.

### Minor

None.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Inventory | Pass | Correct ten types and 129 cards; excluded types absent |
| Setup | Partial | Correct five-card hands/two fields for four players; no five-player or chosen-start setup |
| Hand ordering | Pass | Front planting and append-on-draw preserve order |
| Turn phases | Partial | Normal phase order works; terminal boundaries do not |
| Planting/fields | Pass | Mandatory first, optional second, same-type fields, forced harvest available |
| Reveal | Partial | Two draws modeled; depletion timing is wrong |
| Trading/gifts | Fail | No consent protocol; incomplete quantities and gifts |
| Mandatory planting | Pass | Received and retained reveals must be planted in chosen order |
| Draw phase | Partial | One clockwise draw per player, but third-depletion handling fails |
| Harvesting/yields | Partial | Values and Acker rewards correct; harvest authority is wrong |
| Private information | Fail | All hands are exposed |
| Terminal scoring | Partial | Final harvest and fixed-start tie-break work; terminal timing/setup do not |
| Returns | Pass | Nonterminal zero and documented winner-based terminal returns |

## Missing deterministic scenarios

No test sources were inspected. The module needs deterministic coverage for at least:

- Third depletion caused by the first versus second reveal card.
- Third depletion caused by each position in the phase-4 draw sequence.
- Third depletion when the final phase-4 recipient takes the last card, ensuring no new turn starts.
- First/second depletion while another reveal or draw remains owed, including immediate reshuffle.
- Five-player setup, draw order, field count, and tie-breaking.
- Nonzero configured start player and wraparound tie distances.
- Proposed trade accepted versus rejected, proving no pre-acceptance movement.
- Rejected gift.
- Atomic two-for-one exchange and a gift from an active player's hand.
- Inactive owner harvesting during another turn while the active player cannot harvest that field for them.
- Per-player observations showing own full hand and only opponent counts.
- Ackerbohne harvests of one, two without field 3, two with field 3, and three cards.

## Material questions for a human

- Is an external wrapper expected to provide player-specific observations? None is supplied or referenced, and the module explicitly calls `GameState` public.
- Is action selection centrally mediated outside `current_player` so an inactive owner can initiate only their own harvest? If so, that interface contract must be supplied; the module itself does not enforce it.
- Is the fixed seeded shuffle intentional for replayability, or should chance/seed injection be exposed? The supplied rules require mixing, but the approved facts do not prescribe a simulator randomness API.

These are implementation-interface questions; the gameplay packet itself sufficiently decides the scored issues.

score: 0.42
confidence: high
critical_issues: 1
major_issues: 5
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true