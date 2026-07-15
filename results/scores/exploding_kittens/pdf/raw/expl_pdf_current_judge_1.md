score: 0.42  
confidence: high

The basic setup, ordinary draw flow, Attack/Skip handling, terminal winner, and most card effects are represented. However, eight material rule contradictions remain, including one edge-case crash/deadlock path.

## Findings

### Major

1. Restored actions can crash or deadlock when the target spent its last card during the NÖ! chain.

- Canonical fact: `NOPE-07`
- Evidence type: `human_decision`
- Rule quote, page 2, “NÖ!”: “Alle Karten, die ge-NÖ!-t wurden, sind raus und bleiben auf dem Ablagestapel.”
- Approved decision: if a legal target spends its last card during reactions and the action is restored, resolution completes without a transfer.
- Code: `Game._resolve()` for `"pair"` calls `random.choice(s.hands[target])`; `"play"`/`FAVOR` enters `phase="favor"` even if the target is now empty.
- Expected: restored Pair/Favor resolves with no transfer.
- Implemented: Pair raises an exception on the empty list; Favor produces a nonterminal phase with no legal donation action.

2. Elimination does not discard the eliminated player’s remaining hand.

- Canonical fact: `EXP-03`
- Evidence type: `rule_quote`
- Rule quote, page 2, “Exploding Kitten”: “Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.”
- Code: `Game.apply_action()`, `"Ziehen"` transition without a Defuse.
- Expected: append the Kitten and every remaining hand card to discard, then empty the hand.
- Implemented: only the Kitten is discarded; the eliminated player retains all hand cards.

3. Defusing during an Attack incorrectly removes the remaining owed turn.

- Canonical fact: `DEF-04`
- Evidence type: `human_decision`
- Rule quote, page 2, “Entschärfung”: “Dann ist dein Spielzug beendet.”
- Approved decision: the current individual turn ends, but any further turn owed by Attack must still be taken.
- Code: `"insert"` transition in `Game.apply_action()`.
- Expected: after reinsertion, decrement the attacked player’s obligation and keep that player active if one turn remains.
- Implemented: reinsertion always advances to the next player and resets `turns_left=1`.

4. A five-card combination cannot reliably retrieve one of its own just-discarded components.

- Canonical fact: `FIVE-01`
- Evidence type: `rule_quote`
- Rule quote, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Code: `Game.legal_actions()` generates retrieval choices exclusively from `s.discard` before the five components are discarded.
- Expected: discard the five cards first, then allow any card now in discard—including one of those five—to be selected.
- Implemented: a component is selectable only when an equivalent title was already present. If discard was empty, no five-card action is offered at all.

5. Exploding Kittens and Defuses are excluded from combinations despite the approved unrestricted title rules.

- Canonical facts: `PAIR-01`, `FIVE-01`, `FIVE-02`
- Evidence type: `rule_quote`
- Rule quotes, page 2, “Kombinationen”:
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden …”
  - “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst …”
- Code: `Game.legal_actions()` uses `c not in (EK, DEFUSE)` for pairs/triples and subtracts `{EK, DEFUSE}` from five-card candidates.
- Expected: any qualifying titles are legal; the approved facts explicitly allow a retrieved Kitten to participate in same-title combinations.
- Implemented: both titles are categorically barred from every combination.

6. Triple requests reveal the target’s hand and do not support a genuine named absent-card request.

- Canonical facts: `TRI-01`, `SET-08`
- Evidence type: `rule_quote`
- Rule quotes:
  - Page 2, “Drilling”: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
  - Page 1, setup: “Halte dein Blatt stets verdeckt.”
- Code: `Game.legal_actions()` in `phase=="triple"` enumerates exactly `set(s.hands[s.target])`, plus a generic `"Karte nicht vorhanden"` action.
- Expected: the actor explicitly names a title without learning whether the target holds it; transfer occurs only if present.
- Implemented: legal actions disclose every title in the target’s hand, and an absent request has no named title.

7. Shuffle leaves an earlier top-card preview recorded as current knowledge.

- Canonical fact: `FUT-03`
- Evidence type: `human_decision`
- Rule quote, page 2, “Mischen”: “Misch den Spielstapel sorgfältig neu.”
- Approved decision: a prior preview becomes stale after Shuffle and must not be presented as current top-card knowledge.
- Code: `Game._resolve()`, `card == SHUFFLE`.
- Expected: invalidate affected `GameState.seen` entries.
- Implemented: the deck is shuffled while `seen` remains unchanged.

8. The reaction chain can close before every eligible player has consecutively passed.

- Canonical fact: `NOPE-02`
- Evidence type: `human_decision`
- Rule quote, page 2, “NÖ!”: “Du kannst ein NÖ! auf ein anderes NÖ! legen, um es aufzuheben und daraus ein DOCH! zu machen.”
- Approved interface convention: the chain closes after all eligible living players consecutively pass.
- Code: reaction handling closes after `len(_others(s, s.player))` passes, excluding the original actor from the required count even after a new NÖ! resets the chain.
- Expected: after each NÖ!, complete a full consecutive-pass cycle among all currently eligible participants.
- Implemented: in a three-player game, after one player plays NÖ!, the other two can pass and close the chain before the first player receives another opportunity to play a further NÖ!.

No critical or minor findings.

## Coverage

| Rule area | Result |
|---|---|
| Setup and card counts | Conforms |
| Ordinary turn/draw flow | Conforms |
| Attack and Skip | Mostly conforms; attacked Defuse fails |
| Explosion/elimination | Winner logic conforms; discard cleanup fails |
| Defuse reinsertion | Position/order conform; owed-turn accounting fails |
| Favor | Normal transfer conforms; restored-empty-target deadlocks |
| Future/Shuffle | Preview contents conform; invalidation fails |
| Pair/Triple/Five | Multiple material legal-action and information failures |
| NÖ!/DOCH! | Basic toggling works; closure and empty-target restoration fail |
| Terminal returns | Conforms |
| Public/private information | Triple leaks target titles; preview can remain stale |

## Missing deterministic scenarios

Recommended deterministic coverage:

- Elimination moves the complete hand and Kitten to discard.
- Defuse on the first of two attacked turns preserves the second turn.
- Five-card play with an initially empty discard retrieves one of its components.
- Same-title Defuse pair and retrieved-Kitten combination legality.
- Triple requests a title absent from the target without revealing target contents.
- Shuffle invalidates all stored previews.
- A NÖ! chain completes a full pass cycle after every toggle.
- Restored Pair and Favor against a now-empty target resolve without exception or deadlock.

## Material questions for a human

- Should previews also be invalidated or transformed whenever another player draws a card, not only after Shuffle? The approved facts explicitly decide Shuffle but not every other deck mutation.
- Should the original actor be allowed to NÖ! their own initially proposed action, or only respond after someone else plays NÖ!? Physical reaction priority remains explicitly ambiguous.
- Is `GameState` intended as privileged engine state, or as a player-visible observation? This determines whether publicly accessible hands/deck order are themselves interface violations.

score: 0.42
confidence: high
critical_issues: 0
major_issues: 8
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true