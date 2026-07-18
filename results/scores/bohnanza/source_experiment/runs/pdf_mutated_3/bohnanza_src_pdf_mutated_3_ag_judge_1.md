Score: **0.40**, confidence: **high**. Inventory, planting, trade transfer, harvest values, and Ackerbohne rewards are substantially represented. However, the deck lifecycle ends the game at the first exhaustion, phase 4 draws the wrong cards, and several material timing/information/result rules are contradicted.

## Findings

### Critical

1. **The first empty draw pile ends the game; reshuffles and three-depletion lifecycle are absent.**

   - Canonical facts:
     - `DECK-01`
       - Evidence type: `human_decision`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels. Lege sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
     - `END-01`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - `END-02`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
     - `END-05`
       - Evidence type: `human_decision`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “endet, sobald”
   - Conflicting code: `GameState.end_pending`, `Game._reveal`, `Game._draw_and_advance`.
   - Expected: The first and second exhaustions immediately reshuffle the discard and continue any owed reveal/draw. Only the third exhaustion ends the game, with different boundaries in phases 2 and 4.
   - Implemented: There is no depletion counter and the discard is never reshuffled. `_reveal` sets `end_pending` whenever the deck first becomes empty; `_draw_and_advance` then calls `_finish`. An exhaustion during phase 4 also finishes immediately regardless of whether it is the first, second, or third.
   - Impact: Normal games terminate far too early, and cards in the discard never return to circulation.

### Major

2. **Variant phase 4 deals three cards to the active player instead of one card to every player.**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting code: `legal_actions` action `DRAW_THREE_CARDS`; `Game._draw_and_advance`.
   - Expected: Each player draws exactly one card, active player first and then clockwise, appending it to their ordered hand.
   - Implemented: Up to three cards are appended only to `hands[s.active]`; all other players receive none.
   - Impact: Hand growth, card distribution, turn strategy, and depletion timing are materially changed.

3. **Players cannot exercise the approved anytime-harvest right.**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Conflicting code: `Game.legal_actions`, `Game._voluntary_harvests`, `Game.current_player`.
   - Expected: A field owner may harvest between individual game steps, including during another player’s turn, while respecting the singleton-protection rule and atomic-action boundaries.
   - Implemented: Standalone `HARVEST` actions exist only for the active player in the `trade` phase. Inactive players cannot harvest, and the active player cannot freely harvest between most other steps.
   - Impact: Players can be forced into different harvests or lose valid timing opportunities.

4. **Opponent hand identities are exposed during offer construction.**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar. Jede weitere steckst du dahinter.”
   - Approved complete expectation: The owner sees their whole ordered hand; opponents see only its count unless information is voluntarily communicated.
   - Conflicting code: `GameState.hands`; the `build_offer` branch of `Game.legal_actions`, especially `OFFER_REQUEST_HAND:{i}:{b}`.
   - Expected: An opponent’s ordered card identities remain private.
   - Implemented: Offer actions enumerate every card in the other player’s hand, including its index and bean name. The complete hands are also present in the returned state without a player-specific observation API.
   - Impact: Private information directly affects available-action output. This deviation depends on the approved human privacy decision, rather than an explicit printed statement that hands must be mechanically hidden.

5. **Tie-breaking uses the current active player instead of the original start player.**

   - Canonical fact: `END-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 9
   - Exact evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
   - Conflicting code: `Game._finish`, particularly `order=[(s.active-k)%s.players ...]`.
   - Expected: Among tied players, choose the one with the greatest clockwise seat distance from the original start player.
   - Implemented: Candidates are considered counterclockwise from the player active at termination. The original starter is not used.
   - Impact: Tied games can return the wrong winner.

### Minor

None.

## Rule-area coverage

| Rule area | Status | Assessment |
|---|---|---|
| Player count and inventory | Pass | Correct 4–5 player restriction and 129-card selected deck |
| Initial hands and hand order | Pass/partial | Five ordered cards and append behavior modeled; privacy fails |
| Phase 1 planting | Pass | Mandatory first, optional second, compatible/forced harvest choices |
| Reveal and trading | Mostly pass | Two-card reveal in ordinary cases; consensual unequal trades and pending cards modeled |
| Mandatory traded-card planting | Pass | Pending and retained face-up cards must be planted; order is selectable |
| Phase 4 draw | Fail | Three cards to active player instead of one to every player |
| Deck exhaustion and reshuffle | Fail | No reshuffle or depletion count; game ends on first exhaustion |
| Harvest values/protection | Pass | Normal meters and singleton protection agree with approved facts |
| Harvest timing | Fail | Anytime/out-of-turn harvesting is unavailable |
| Ackerbohne | Pass | One/two/three-card outcomes and third-field persistence agree |
| Terminal scoring and returns | Partial | Final harvest and winner returns exist; tie-break and end timing fail |
| Elimination | Pass | No elimination mechanism |
| Private observation | Fail | Opponent card identities are exposed |

## Missing deterministic scenarios

- First exhaustion during a two-card reveal with exactly one card left: reshuffle and reveal the second card.
- First and second exhaustion during phase 4: reshuffle and continue the owed clockwise one-card draws.
- Third exhaustion during phase 2: finish trading and all phase-3 planting, skip phase 4, then score.
- Third exhaustion during phase 4: stop immediately after the exhausting player’s draw.
- Four- and five-player phase-4 distribution: exactly one appended card per player in clockwise order.
- Inactive-player harvesting between another player’s atomic steps, including singleton-protection cases.
- Player-specific observations and offer actions that reveal only opponent hand counts.
- Ties involving multiple seat combinations and different terminal active players, always anchored to the original starter.
- Ackerbohne harvests of one, two with/without field 3, and exactly three.

## Material questions for a human

- Is player index `0` intended to canonically represent the chosen start player? If so, that convention should be documented and retained explicitly for tie-breaking.
- What engine-level interrupt mechanism should expose out-of-turn harvest choices between atomic actions?
- Should trade requests name a bean type, with the responding owner selecting the actual hand card, or use another private-action protocol? The present indexed, bean-labelled actions disclose the hand.

```text
score: 0.40
confidence: high
critical_issues: 1
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```