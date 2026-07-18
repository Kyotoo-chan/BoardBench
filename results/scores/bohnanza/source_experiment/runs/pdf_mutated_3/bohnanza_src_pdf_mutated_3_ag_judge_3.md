## Review result

`score: 0.40` — `confidence: high`

The module models the selected 129-card inventory, ordered hands, planting, bilateral trade consent, field compatibility, bean meters, Ackerbohne rewards, and basic scoring reasonably well. However, it ends on the first deck depletion instead of the third and never reshuffles the discard pile. The variant draw phase, tie-break, harvesting windows, and private-information boundary also materially contradict approved facts.

## Findings

### Critical

1. Deck recycling and the three-depletion game clock are absent

- Canonical facts:
  - `DECK-01`
    - Evidence type: `human_decision`
    - Source: `RULES`, PDF page 9
    - Exact evidence: “Ziehst du die letzte Karte … mische die Karten des Ablagestapels.”
  - `END-01`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF page 9
    - Exact evidence: “endet, sobald der Nachziehstapel zum dritten Mal leer wird”
  - `END-02`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF page 9
    - Exact evidence: “beim Aufdecken … spielt ihr die 2. und die 3. Phase noch zu Ende”
  - `END-05`
    - Evidence type: `human_decision`
    - Source: `RULES`, PDF page 9
    - Exact evidence: “endet, sobald”
- Conflicting symbols/transitions: `GameState` has no depletion counter; `_reveal`, `_draw_and_advance`, and `end_pending`.
- Expected: The first and second depletion immediately shuffle the discard pile and continue any owed draw. Only the third depletion ends the game, with different phase-2 and phase-4 boundaries.
- Implemented: `_reveal` merely takes `min(2, len(deck))`; `_draw_and_advance` similarly draws only what remains. Neither method recycles `discard`. `end_pending` becomes true whenever the initial deck first empties, and `_draw_and_advance` then calls `_finish`.
- Impact: The game reliably terminates roughly two deck cycles early, discarded cards never return, and the resulting winner can be fundamentally wrong.

### Major

2. Variant phase 4 gives three cards to the active player instead of one to every player

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “zieht jeder von euch eine Karte … aktive Spieler … im Uhrzeigersinn”
- Conflicting symbols/transitions: `legal_actions` emits `DRAW_THREE_CARDS`; `_draw_and_advance`.
- Expected: Each player draws one card, beginning with the active player and proceeding clockwise; each card is appended to its recipient’s hand.
- Implemented: `hs[s.active].extend(s.deck[:n])`, where `n=min(3,len(s.deck))`. Only the active player receives cards.
- Impact: Hand sizes, private resources, depletion timing, and future turns all diverge materially.

3. Tie-breaking uses the current active player rather than the original start player

- Canonical fact: `END-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Bei einem Gleichstand … im Uhrzeigersinn am weitesten weg vom Startspieler”
- Conflicting symbol: `_finish`, particularly `order=[(s.active-k)%s.players ...]`.
- Expected: Among tied players, select the one with the greatest clockwise seat distance from the original start player.
- Implemented: Search starts at the player active when scoring begins and proceeds in reverse seat order.
- Impact: Tied games can return the wrong winner.

4. Opponents’ private hand identities leak through the state and legal-action list

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte … ist die vorderste Karte.”
- Approved completion: The owner sees the whole ordered hand; opponents see only its count unless players voluntarily communicate.
- Conflicting symbols: public `GameState.hands`; `legal_actions` in `build_offer`, especially `OFFER_REQUEST_HAND:{i}:{b}`; absence of a player-specific observation method.
- Expected: An observer receives their own ordered hand and only opponents’ hand counts. Voluntary communication must not become automatic disclosure.
- Implemented: All hands are stored directly in exposed state, and an active player’s legal actions enumerate every card name and index in the proposed recipient’s hand.
- Impact: Trading decisions can use hidden information unavailable under the approved information model.

5. Most permitted harvesting windows are unavailable

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “jederzeit … auch wenn du nicht der aktive Spieler bist”
- Conflicting symbols/transitions: `_voluntary_harvests`, `legal_actions`, and the initial `HARVEST:` branch in `apply_action`.
- Expected: Any owner may harvest between individual game steps, including during another player’s turn, except inside an executing atomic draw or transfer.
- Implemented: Explicit voluntary `HARVEST` actions are offered only to the active player during `trade`. Other players cannot harvest, and the active player cannot voluntarily harvest between hand plants, offer-building steps, trade responses, mandatory traded-card plants, or draws. Integrated `HARVEST_AND_PLANT` only handles a forced planting target.
- Impact: Legal field-management choices and their timing are materially absent.

### Minor

None identified from the permitted evidence.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Pass | 4–5 players, two initial fields, five cards each, and the 129-card selected inventory are represented. |
| Hand order | Partial | Front planting and draw appending work, but private observation does not. |
| Turn phases | Partial | Phase order is recognizable; phase 4 is materially wrong. |
| Hand planting | Pass | First mandatory, second optional, third forbidden; legal forced harvest targets exist. |
| Reveal | Partial | Reveals up to two, but cannot recycle the discard to complete an owed reveal. |
| Trading | Pass/partial | Active-player bilateral, consensual, unequal trades and gifts are represented; hidden cards leak. |
| Mandatory planting | Pass | Pending and retained revealed cards must be planted, with selectable order. |
| Harvesting | Partial | Protection, meters, emptying, and Acker rewards work; timing access is incomplete. |
| Chance/deck lifecycle | Fail | No reshuffle or depletion count. |
| End conditions | Fail | First depletion ends the game; phase-specific third-depletion boundaries are missing. |
| Scoring/returns | Partial | Final field harvest and winner returns exist; tie-break is wrong. |
| Elimination | Pass | None implemented. |

## Missing deterministic scenarios

- First depletion during a two-card reveal: reshuffle discard and retrieve the remaining owed card.
- First and second depletion during phase-4 draws: recycle and continue the clockwise draw sequence.
- Third depletion during phase 2: finish trading and mandatory planting, skip phase 4, then score.
- Third depletion during phase 4: stop after the exact draw that empties the pile; later players do not draw.
- Four- and five-player phase 4: verify exactly one appended card per player in clockwise order.
- Tie among multiple seats with a fixed original start player.
- Observer views and legal actions: own ordered hand visible, opponent identities absent.
- Non-active-player harvest between two mandatory planting steps.
- Active-player voluntary harvest before a mandatory card that already has a compatible field.
- Singleton protection across two and three fields.
- Ackerbohne harvests at one, two without field 3, two with field 3, and three cards.
- Trade acceptance preserves the order of every untraded hand card and moves received cards only to pending planting.

## Material questions for a human

- Is a separate player-specific observation adapter supplied outside `implementation.py`? None exists in the reviewed module, while both `GameState.hands` and trade action names disclose opponent cards.
- Is seat 0 intentionally the preconfigured start player for every environment instance? If start-player choice must be externally configurable, the constructor currently has no such parameter.

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