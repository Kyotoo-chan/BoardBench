Score: **0.76**, confidence: **high**. The module correctly implements the selected 4–5-player, 129-card Ackerbohne variant, including inventory, ordered hands, phase sequencing, yields, reshuffling, Ackerbohne harvests, third-depletion timing, final scoring, and tie-breaking. Two material gaps remain: out-of-turn harvesting and observable trade consent.

## Findings

### Major — Out-of-turn harvesting is unavailable

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7, “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting symbols: `legal_actions`, `_harvest_actions`, `current_player`
- Expected: Between atomic steps, any player may choose to harvest one of their own legal fields, including during another player’s turn.
- Implemented: Harvest actions are generated only for `state.decision`. During normal active-player decisions, other players have no way to interrupt and harvest. A trade partner gets harvesting access only while they happen to be the consent decision-maker.
- Impact: Players can lose strategically relevant harvest timing during reveals, negotiations, other players’ planting, and phase-4 draws.

### Major — A trade partner cannot observe the proposed terms through `render`

- Canonical fact: `TRADE-05`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 6, “Denn beide Spieler müssen dem Handel zustimmen.”
- Conflicting symbols: `TradeDraft.awaiting_consent`, `legal_actions`, `render`
- Expected: When the partner must accept or reject, the observation must identify the exact cards offered and requested so consent applies to the proposed atomic transfer.
- Implemented: `render` omits `state.trade` entirely. At the consent decision, the partner receives `("Handel annehmen",)` and `("Handel ablehnen",)` but cannot see the selected offered-hand, revealed, and requested-hand indices through the rendered observation.
- Impact: Consent can be blind, particularly when an offered card comes from the active player’s private hand.

### Minor — Start player is implicitly fixed rather than configured

- Canonical fact: `SET-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 2, “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
- Conflicting symbols: `Game.__init__`, `initial_state`, `_finish`
- Expected: A chosen/configured start player acts first and remains identifiable for the final tie-break.
- Implemented: Player 0 is always active initially, and `_finish` assumes player 0 was the start player. No start-player setting or marker is exposed.
- Impact: Seat relabelling can work around this, so core outcomes remain correct if player 0 is documented as the selected start player.

### Question — Randomness is external to the copied state

`_draw_one` mutates `self._rng` during discard reshuffles. Applying actions to alternate copies of the same `GameState` can therefore depend on earlier branch evaluation. The packet specifies shuffling but does not define whether evaluator-facing transitions must be replayable solely from state, so this is not scored as a contradiction.

## Rule-area coverage

| Area | Status | Notes |
|---|---|---|
| Setup and inventory | Mostly correct | 4–5 players, two initial fields, five ordered cards, and all 129 cards are correct; start player is fixed to index 0. |
| Hand order/privacy | Correct | Front planting and append-only draws are correct; rendered opponents expose counts only. |
| Turn and phase flow | Correct | Four phases and clockwise succession are implemented. |
| Reveal and trade | Partial | Two-card reveal and atomic transfers are correct; consent observation lacks trade terms. |
| Mandatory planting | Correct | All received and retained revealed cards enter the queue; owner chooses among their queued cards. |
| Drawing/reshuffling | Correct | One draw per player, reshuffle after first/second depletion, and third-depletion timing match approved decisions. |
| Harvesting | Partial | Protection, yields, discards, and emptying fields are correct; arbitrary owners cannot harvest between steps. |
| Ackerbohne | Correct | One, two, and three-card harvest results and third-field persistence are correct. |
| Terminal scoring | Correct | Final harvest, ignored hands, raw coins, third-depletion endings, and distance-from-player-0 tie-break are implemented. |
| Returns | Correct | Nonterminal zero and terminal winner-based `+1/-1` returns are permitted. |

## Missing deterministic scenarios

- A non-active, non-decision player harvesting between two atomic actions.
- Each non-active player harvesting between separate phase-3 plant steps.
- Trade acceptance where the active player offers a private hand card, verifying that the partner observes its identity and all requested cards.
- A gift in each direction, confirming recipient consent and sideways placement.
- First or second depletion on the first reveal, followed by the owed second reveal from the reshuffled discard.
- Third depletion on the first phase-2 reveal, confirming no replacement draw but completion of trade and phase 3.
- Third depletion during phase 4, confirming immediate termination before the next player draws.
- Ackerbohne harvests of one, two without field 3, two with field 3, and three.
- A final-score tie involving the original start player and multiple clockwise seats.
- Replay of identical pre-reshuffle states to establish the intended RNG/branching contract.

## Material questions for a human

- Is player index 0 an accepted documented representation of the chosen start player, or must callers be able to configure another index?
- Does the host expose only `render`, or can a consenting player inspect `GameState.trade` directly? If only `render` is visible, trade terms must be added to that observation.
- Must transitions be reproducible from `GameState` alone, or is a mutable game-level RNG acceptable?

score: 0.76
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
