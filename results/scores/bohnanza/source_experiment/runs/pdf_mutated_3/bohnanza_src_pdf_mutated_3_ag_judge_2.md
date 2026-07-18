## Assessment

Score: **0.36**  
Confidence: **high**

The inventory, ordered-hand mutation, phases 1–3, trade consent, crop meters, singleton protection, and Ackerbohne rewards are substantially represented. However, the deck lifecycle ends the game at the first depletion, variant drawing is fundamentally wrong, permitted harvest timing is missing, private hands leak, and tie-breaking can select the wrong winner.

## Findings

### Critical — First deck depletion ends the game; reshuffling is absent

- Canonical facts:
  - `DECK-01`
    - Evidence type: `human_decision`
    - Source: `RULES`, PDF p.9
    - Evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels. Lege sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
  - `END-01`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF p.9
    - Evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting code: `GameState.end_pending`, `Game._reveal`, `Game._draw_and_advance`.
- Expected: First and second depletion immediately reshuffle the discard pile and continue any owed draw. Only the third depletion ends the game, with phase-dependent timing.
- Implemented: Any empty deck sets `end_pending`; the following draw calls `_finish`. There is no depletion counter and no discard reshuffle. A reveal also uses `min(2, len(deck))`, so it can reveal only one card instead of reshuffling to complete the owed two.
- Impact: Most games terminate after only one pass through the deck, materially changing duration, strategy, scores, and winner.

### Major — Variant phase 4 gives three cards to one player

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF p.10
- Evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
- Conflicting code: `legal_actions` exposes `DRAW_THREE_CARDS`; `_draw_and_advance` appends up to three cards only to `s.active`.
- Expected: Every player draws one card, active player first and then clockwise, with each card appended to its recipient’s hand.
- Implemented: The active player draws up to three; all other players draw none.

### Major — General voluntary harvesting is unavailable

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF p.7
- Evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting code: `legal_actions`, `_voluntary_harvests`; voluntary `HARVEST` actions are added only for the active player during `phase == "trade"`.
- Expected: A field owner may harvest between individual atomic game steps, including during another player’s turn.
- Implemented: Inactive players never receive voluntary harvest actions. The active player cannot voluntarily harvest during most phases; only forced harvest-and-plant transitions remain available.
- Provenance note: The exact between-step timing is an approved human decision, not solely printed-rule detail.

### Major — Opponents’ private hand identities leak

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF p.3
- Evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
- Approved expectation: The owner sees the complete ordered hand; opponents see only its count unless information is communicated voluntarily.
- Conflicting code:
  - Public `GameState.hands` contains every ordered hand.
  - `legal_actions` iterates through `s.hands[o.other]` and emits `OFFER_REQUEST_HAND:{index}:{bean}`, exposing every requested opponent card’s identity.
  - No player-specific observation function exists.
- Expected: Opponent observations and action descriptions must not reveal card identities.
- Implemented: Raw state and legal-action names expose them.
- Provenance note: This is an adjudication-dependent information-model deviation.

### Major — Tie-breaking can choose the wrong winner

- Canonical fact: `END-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF p.9
- Evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
- Conflicting code: `Game._finish`, specifically `order=[(s.active-k)%s.players ...]`.
- Expected: Among tied players, select the player with greatest clockwise seat distance from the original start player.
- Implemented: Selection starts from the terminal active player and traverses backward, so it depends on who happened to be active at termination. For example, with four players, start player 0, terminal active player 2, and a tie between seats 2 and 3, the code chooses 2; the rule chooses 3.

### Question — Is seat 0 externally defined as the chosen start player?

`initial_state` always makes player 0 active, and the constructor has no start-player parameter or marker state. This is not scored because an external seat-assignment convention could designate seat 0 as the chosen start player. The integration contract should state that explicitly.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup/inventory | Mostly covered | Correct 4–5 players, 129-card deck, five cards, two fields; start-player configuration unclear |
| Ordered hands | Partial | Planting/trade removals preserve order; privacy is not enforced |
| Phase 1 planting | Covered | Mandatory first, optional second, no third; empty hand skips |
| Reveal/trading | Mostly covered | Two-card reveal works only when deck has enough cards; consent and unequal exchanges work |
| Mandatory planting | Covered | Pending and retained face-up cards must be planted; order is selectable |
| Variant phase 4 | Failed | Active player draws three instead of everyone drawing one |
| Deck/chance | Failed | No reshuffle or depletion count |
| Harvest payouts | Covered | Normal meters, protection, and Ackerbohne cases align with approved facts |
| Harvest timing | Failed | Broad between-step/inactive-player harvesting absent |
| Terminal scoring | Partial/failed | Final fields harvested and hands ignored; trigger and tie-break are wrong |
| Returns | Partial | Nonterminal zero and terminal ±1 are acceptable, but winner can be wrong |

## Missing deterministic scenarios

- First depletion with one reveal still owed: reshuffle discard, reveal the second card, and continue.
- First and second depletion during phase 4: reshuffle and complete the remaining clockwise one-card draws.
- Third depletion during reveal: complete phases 2 and 3, skip phase 4, then score.
- Third depletion during phase 4: stop immediately after the emptying draw; later players do not draw.
- Four- and five-player phase 4 draw order, verifying one appended card per player.
- Inactive-player harvest between steps and active-player voluntary harvest outside trading.
- Singleton protection across voluntary and forced harvests.
- Player-specific observations and trade actions proving that opponent card identities remain hidden.
- Tie cases across different terminal active players and different tied seat sets.
- Explicit nonzero chosen start-player setup, if supported by the surrounding API.

## Material questions for a human

- Does the host framework treat `GameState` as privileged internal state, and if so, what player-specific observation method is required? Even with privileged state, the current legal-action strings disclose opponent cards.
- Is seat 0 contractually the already-chosen start player, or must the module accept a start-player setting?
- No supplied rulebook issue requires clarification; the principal defects contradict approved facts or approved human decisions.

score: 0.36
confidence: high
critical_issues: 1
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true