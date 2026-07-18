score: 0.16  
confidence: high

The module implements a recognizable base-game skeleton, but not the approved 129-card Ackerbohne condition. It also permits repeated reveals, uses the wrong variant draw phase, and does not preserve consent, ownership, or private information during trades.

## Findings

### Critical

1. **The approved Ackerbohne condition is replaced by the 104-card base game.**

   - Canonical facts:
     - `INV-03`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 10
       - Evidence: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen”
     - `INV-04`
       - Evidence type: `user_observation`
       - Source: `COMPONENTS`, `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`
       - Evidence: Weinbrandbohne `22`; Ackerbohne `3`
     - `ACKER-01`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 11
       - Evidence: “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
   - Conflicting symbols/transitions: `BEANS`, `Game.initial_state`, every `range(2)` field loop, `_harvest`.
   - Expected: Eight base types plus 22 Weinbrandbohnen and three Ackerbohnen, totaling 129 cards. Harvesting exactly two Ackerbohnen can unlock a persistent third field; the special one-, two-, and three-card harvest outcomes must exist.
   - Implemented: `BEANS` contains only the eight base types totaling 104 cards. Every player is permanently restricted to two fields, and no Ackerbohne behavior exists.
   - Impact: This is a different source condition with different deck probabilities, planting decisions, field capacity, scoring, depletion timing, and potentially winner.

2. **Phase 2 can reveal more than one pair, potentially exhausting the deck in one turn.**

   - Canonical fact: `P2-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 5
   - Evidence: “Ziehe die obersten zwei Karten vom Nachziehstapel und lege sie für alle sichtbar aufgedeckt daneben.”
   - Conflicting symbols/transitions: `Game.legal_actions` phase-2 branch and the trade/gift transitions that `pop` from `s.exposed`.
   - Expected: The active player reveals exactly two cards once, then trades or retains those cards.
   - Implemented: Reveal availability is inferred from `not s.exposed`. After both revealed cards are transferred, `s.exposed` becomes empty and “Zwei Bohnenkarten aufdecken” becomes legal again. The cycle can repeat during the same phase.
   - Impact: A common legal trading sequence can become an unlimited reveal cycle, radically changing chance, depletion, end timing, and winner.

### Major

3. **The Ackerbohne phase-4 draw rule is replaced by the base-game three-card draw.**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Evidence: “zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting symbols/transitions: `("Drei Bohnenkarten nachziehen",)` and its `for _ in range(3)` transition.
   - Expected: Every player draws one card, active player first and then clockwise; each draw appends to that player’s hand.
   - Implemented: Only the active player draws three cards.
   - Impact: Materially changes every player’s hand growth, private information, draw order, and third-depletion timing.

4. **Trades are executed unilaterally without explicit proposal and accept/reject states.**

   - Canonical fact: `TRADE-05`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 6
   - Evidence: “beide Spieler müssen dem Handel zustimmen”
   - Conflicting symbols/transitions: `Bohnenhandel`, `Bohnenhandel 2 gegen 1`, and `Bohnenkarte schenken` in `apply_action`.
   - Expected: A proposal leaves cards in place until the other participant explicitly accepts; rejection must also be possible. The approved executable convention expressly requires proposal and accept/reject actions.
   - Implemented: Selecting the action immediately removes and transfers cards. The comment asserting acceptance does not provide the other player with a decision.
   - Impact: The active player can force trades or gifts that the recipient never accepted.

5. **Trade actions reveal and let the active player select opponents’ private cards.**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
   - Approved complete fact: Each owner sees their whole ordered hand; opponents see only its count unless voluntarily communicated.
   - Conflicting symbols/transitions: `Game.legal_actions`, particularly `enumerate(s.hands[q])`, which embeds `j` and `wanted` bean identity in actions offered while `current_player` remains the active player.
   - Expected: An inactive player chooses which own card to offer; the active player cannot inspect or directly select an uncommunicated card by type and position.
   - Implemented: Legal actions enumerate every card type and index in every opponent’s hand. `render` hides those hands, but the action list discloses them anyway.
   - Impact: Private information and trade agency are materially broken.

6. **Several legal unequal exchanges and gifts are absent.**

   - Canonical facts:
     - `TRADE-04`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 5
       - Evidence: “mit einer unterschiedlichen Kartenanzahl handeln”
     - `TRADE-07`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 6
       - Evidence: “Bohnenkarten schenken … muss … zustimmen”
   - Conflicting symbol: Phase-2 action generation in `Game.legal_actions`.
   - Expected: Consensual nonempty gifts can travel in either direction between the active player and another player, and exchanges may use differing quantities.
   - Implemented: Gifts only originate from the active player. Exchanges are limited to one-for-one and active-player two-for-one; inactive-to-active gifts, one-for-two, and larger unequal exchanges are absent.
   - Impact: Material legal trade options are missing.

7. **Recipients cannot choose the order in which their newly acquired cards are planted.**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 7
   - Evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting symbols/transitions: Phase-3 `owners[0]`, `s.pending[q][0]`, `s.exposed[0]`, and `Neue Bohnenkarte anbauen`.
   - Expected: Each recipient chooses the next card among all cards they must plant, including necessary harvest decisions between individual plantings.
   - Implemented: Players are processed by numeric seat order. Each player’s `pending` queue is fixed, and the active player’s pending cards must precede retained exposed cards. `current_player` also remains the active player while choosing fields for inactive recipients.
   - Impact: Planting order often determines which fields must be harvested and therefore affects scoring.

8. **The active-player action interface controls other players’ optional harvests.**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Conflicting symbols: `current_player` and the global `("Ernten", p, f)` actions generated for every player.
   - Expected: A field’s owner decides whether and which own field to harvest between atomic steps.
   - Implemented: `current_player` always identifies the turn’s active player, but that actor receives harvest actions targeting every player’s fields.
   - Impact: Optional scoring and field-clearing decisions can be made by the wrong player.

## Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Player count and initial fields | Partial | Correctly accepts 4–5 and starts with two fields |
| Selected inventory | Fail | Uses 104 base cards instead of 129-card Acker condition |
| Ordered hands | Partial | Front removal and back appending work; observations leak through actions |
| Phase-1 planting | Mostly covered | Mandatory first and optional second are represented |
| Reveal phase | Fail | Reveal pair can be repeated |
| Trading | Fail | Consent, privacy, gifts, and exchange quantities are incorrect/incomplete |
| Mandatory planting | Fail | New-card order and recipient agency are missing |
| Variant draw phase | Fail | Active player draws three instead of everyone drawing one |
| Normal harvesting | Partial | Base thresholds and singleton protection are represented |
| Acker harvesting/field 3 | Absent | No special rewards or third field |
| Depletion/end timing | Partial | Third-depletion phase-2/phase-4 branches exist, but operate over wrong draws/deck |
| Final harvest/scoring | Mostly covered | Final harvest, hand exclusion, coins, and fixed-seat tie-break are represented |
| Returns | Covered | Zero nonterminal and winner-based terminal returns |
| Elimination | Covered | No elimination mechanism |

## Missing deterministic scenarios

- Initial deck contains exactly 129 cards before dealing, including 22 Weinbrandbohnen and three Ackerbohnen.
- Harvesting one, two, and three Ackerbohnen, both before and after field 3 has been unlocked.
- Trading away both revealed cards does not make another reveal action legal.
- Phase 4 with four and five players: one draw per player in clockwise order.
- Third depletion on each individual phase-4 player draw, confirming later players do not draw.
- Proposed trade rejection leaves all cards unchanged; acceptance transfers atomically.
- An inactive player gifts a hand card to the active player.
- One-for-two and larger unequal consensual exchanges.
- Opponent legal-action and observation output contains hand counts but no hidden card identities or positions.
- A recipient chooses different planting orders for multiple received/revealed cards.
- An inactive owner, rather than the active player, chooses whether to harvest between steps.
- Tie scoring with a configured start player other than seat 0.

## Material questions for a human

- Is seat `0` contractually defined by the surrounding API as the already chosen start player? If not, setup needs an explicit start-player parameter and persistent original-start identity.
- Is `current_player` intended to identify the sole decision-maker, or is there an undocumented multi-actor action protocol? The current interface otherwise assigns inactive players’ planting and harvesting choices to the active player.

score: 0.16
confidence: high
critical_issues: 2
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true