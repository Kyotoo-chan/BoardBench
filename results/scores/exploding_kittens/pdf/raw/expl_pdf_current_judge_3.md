## 1. Score

**Score: 0.48 — confidence: high.**

Setup, ordinary turns, Attack, Skip, Defuse insertion positions, basic card effects, terminal detection, and returns are substantially implemented. However, seven material rule contradictions affect attacked turns, elimination cleanup, combinations, triple privacy/timing, Nope reactions, and restored actions. The most common game path remains playable, so none rises to `critical`.

## 2. Findings

### Major

1. **Defusing during an Attack incorrectly erases the remaining owed turn**

- Canonical fact ID: `DEF-04`
- Evidence type: `human_decision`
- Rule quote: “Dann ist dein Spielzug beendet.” — page 2, **Entschärfung**
- Approved decision: a Defuse ends the current individual turn, but any further turn owed by Attack must still be taken.
- Conflicting transition: `apply_action`, insert phase, line 137:
  `s.player=self._next(s,p); s.turns_left=1`
- Expected: after reinsertion on the first of two attacked turns, the same player begins the second owed turn.
- Implemented: reinsertion always advances clockwise and resets the obligation to one turn.

2. **Elimination does not move the eliminated player’s remaining hand to discard**

- Canonical fact ID: `EXP-03`
- Evidence type: `rule_quote`
- Rule quote: “Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.” — page 2, **Exploding Kitten**
- Conflicting transition: `apply_action`, lines 159–162.
- Expected: append the Kitten and every remaining hand card to discard, then empty the eliminated hand.
- Implemented: only the Kitten is discarded; the eliminated player retains an inaccessible hand. This also changes later five-card retrieval possibilities.

3. **Five-card combinations cannot retrieve one of their own just-discarded components**

- Canonical fact ID: `FIVE-01`
- Evidence type: `rule_quote`
- Rule quote: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” — page 2, **Kombinationen / Fünfling**
- Conflicting symbols: `legal_actions`, lines 89–94; component discard at lines 175–177.
- Expected: the five components enter discard before retrieval, so each component is an eligible retrieval choice. A five-card combination is therefore possible even when discard was previously empty.
- Implemented: retrieval choices are generated only from the pre-action `s.discard`. If it is empty, no five-card action exists; otherwise the newly discarded components are unavailable unless an equivalent title was already present.

4. **Combination eligibility wrongly excludes Exploding Kittens and Defuses**

- Canonical fact IDs: `PAIR-01`, `FIVE-01`, `FIVE-02`
- Evidence types: `rule_quote` for `PAIR-01` and `FIVE-01`; `human_decision` for `FIVE-02`
- Rule quotes:
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.” — page 2, **Kombinationen / Pärchen**
  - “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst …” — page 2, **Kombinationen / Fünfling**
  - “Wenn du ein Exploding Kitten ziehst …” / “eine beliebige Karte aus dem Ablagestapel nehmen” — pages 1–2; approved decision explicitly permits a retrieved Kitten in same-title combinations.
- Conflicting symbol: `legal_actions`, lines 85–89:
  `c not in (EK, DEFUSE)` and `set(h) - {EK, DEFUSE}`.
- Expected: equal-title Defuses qualify for pairs/triples; retrieved Kittens may participate in same-title combinations. Five distinct titles have no approved Kitten/Defuse exclusion.
- Implemented: both titles are categorically excluded from every combination type.

5. **A triple’s requested title is chosen after the Nope window and leaks the target’s private hand**

- Canonical fact IDs: `NOPE-06`, `TRI-01`, `TRI-02`, `SET-08`
- Evidence types: `human_decision` for `NOPE-06`; `rule_quote` for the others
- Rule quotes:
  - “Mit NÖ! setzt du eine andere Karte und deren Aktion außer Kraft.” — page 2, **NÖ!**
  - “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.” — page 2, **Drilling**
  - “Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine solche Karte, hast du Pech gehabt.” — page 2, **Drilling**
  - “Halte dein Blatt stets verdeckt.” — page 1, **Spielaufbau**
- Approved decision: target and requested title are announced before reactions.
- Conflicting symbols:
  - Triple pending tuple omits the request at lines 171–174.
  - `_resolve` opens a later `triple` phase at line 127.
  - `legal_actions` derives request choices directly from `s.hands[s.target]` at line 72.
- Expected: the actor names any title without seeing whether the target holds it, then the full proposed action enters the reaction window.
- Implemented: the request happens after reactions; available actions reveal every title currently in the target’s private hand. An absent title cannot be named—only an unlabelled “not present” outcome can be selected.

6. **A restored Favor or Pair can deadlock or crash after the target spends its last card as Nope**

- Canonical fact ID: `NOPE-07`
- Evidence type: `human_decision`
- Rule quote: “Alle Karten, die ge-NÖ!-t wurden, sind raus und bleiben auf dem Ablagestapel.” — page 2, **NÖ!**
- Approved decision: if a legal target spends its last card during the reaction chain and the action is restored, it resolves without a transfer.
- Conflicting symbols:
  - Favor resolution opens `phase="favor"` unconditionally at line 123; line 70 then returns no legal donation actions.
  - Pair resolution calls `random.choice(s.hands[target])` unconditionally at lines 124–126.
- Expected: restored action completes with no transfer.
- Implemented: Favor enters a phase with zero legal actions; Pair raises an exception by choosing from an empty list.

7. **The reaction cycle can skip an eligible living responder**

- Canonical fact ID: `NOPE-03`
- Evidence type: `human_decision`
- Rule quote: “Du kannst ein NÖ! auch spielen, wenn du nicht an der Reihe bist.” — page 2, **NÖ!**
- Approved convention: every eligible living player receives a deterministic clockwise opportunity, and the chain closes after all eligible players consecutively pass.
- Conflicting symbols: `_reaction`, lines 102–108, and reaction advancement, lines 145–153.
- Expected: responders are traversed clockwise, without substituting the acting player for an unvisited responder.
- Implemented: the first responder is always the numerically first entry in `_others`, while subsequent responders use `_next`; closure counts passes against the number of non-actors. For three players with actor 1, responders proceed `0 → 1`, then the chain closes after two passes and living player 2 never receives an opportunity.

### Minor

8. **Shuffle retains stale preview metadata**

- Canonical fact ID: `FUT-03`
- Evidence type: `human_decision`
- Rule quote: “Misch den Spielstapel sorgfältig neu.” — page 2, **Mischen**
- Conflicting symbols: Shuffle changes `s.deck` at lines 120–121 but leaves `s.seen` unchanged.
- Expected: an earlier preview must no longer be represented as current top-card knowledge after Shuffle.
- Implemented: the old tuple remains in `s.seen`. This is minor because it currently does not affect legal actions or rendering.

## 3. Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Setup and card counts | Good | Deals 7 plus one Defuse; correct Kitten and two-player Defuse counts |
| Ordinary turn/draw | Good | Zero-or-more plays and mandatory draw supported |
| Attack and Skip | Partial | Ordinary obligations work; Defuse incorrectly erases an owed turn |
| Explosion/elimination | Partial | Automatic Defuse and terminal detection work; hand cleanup is wrong |
| Defuse reinsertion | Partial | Explicit positions and relative deck order work; attacked continuation fails |
| Favor/See/Shuffle | Partial | Main effects work; restored empty Favor deadlocks and preview metadata persists |
| Pairs/triples/fives | Poor | Several legal components excluded; triple timing/privacy wrong; self-retrieval absent |
| Nope reactions | Partial | Toggle/discard behavior exists; responder traversal and empty-target restoration fail |
| Private information | Partial | Render hides identities, but triple legal actions expose target titles |
| Terminal result/returns | Good | Immediate sole-survivor terminal state and `+1/-1` returns |

## 4. Missing deterministic scenarios

- First attacked turn draws a Kitten, Defuses, reinserts, then must take the second turn.
- Eliminated player’s complete remaining hand and Kitten enter discard.
- Five distinct cards with an initially empty discard retrieve one just-played component.
- Five-card retrieval selects each of the five newly discarded component titles.
- Pair/triple made from Defuses and from retrieved Exploding Kittens.
- Triple requests a title absent from the target’s hand without exposing target contents.
- Triple’s requested title is fixed before the Nope window.
- Favor and Pair restored after the target spends its last card as Nope resolve without transfer.
- Three- or four-player reaction chain where the actor is not player 0; verify every eligible responder gets an opportunity.
- Shuffle invalidates prior `seen` metadata.

## 5. Material questions for a human

- Is `GameState` intended as trusted omniscient engine state, or as player-visible observation? If player-visible, its raw `hands` and global `seen` mapping create additional private-information violations.
- In the turn-based Nope convention, should the acting player receive an initial pass opportunity, or only become eligible after another player has played Nope? This affects the precise reaction schedule, though it does not excuse skipping an out-of-turn responder.

score: 0.48
confidence: high
critical_issues: 0
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true