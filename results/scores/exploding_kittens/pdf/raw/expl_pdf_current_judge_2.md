Score: **0.50**, confidence: **high**. The implementation supports the main setup, ordinary turns, most named-card effects, elimination-based termination, and returns. However, seven material rule deviations affect Attack obligations, discard state, combinations, private information, NÖ! resolution, and preview validity.

## Findings

### Major

1. **Defusing during an Attack incorrectly cancels the remaining owed turn**

   - Canonical fact: `DEF-04`
   - Evidence type: `human_decision`
   - Rule quote, page 2, Entschärfung: “Dann ist dein Spielzug beendet.”
   - Approved decision: “any further turn owed by Attack must still be taken.”
   - Code: `apply_action`, `phase == "insert"` transition.
   - Expected: after reinsertion, one individual turn ends; if the player still owes another Attack turn, that same player begins it.
   - Implemented: reinsertion always sets `player = _next(s, p)` and `turns_left = 1`, transferring play and erasing any remaining Attack obligation.

2. **Elimination does not discard the eliminated player’s hand**

   - Canonical fact: `EXP-03`
   - Evidence type: `rule_quote`
   - Rule quote, page 2, Exploding Kitten: “Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.”
   - Code: `apply_action`, exploding draw without Defuse.
   - Expected: the Kitten and every remaining hand card enter the discard pile.
   - Implemented: only `EK` is appended to `discard`; the eliminated player’s cards remain in `hands[p]`. Those cards consequently cannot be retrieved from the discard by a five-card combination.

3. **Five-card combinations cannot retrieve one of their just-discarded components**

   - Canonical fact: `FIVE-01`
   - Evidence type: `rule_quote`
   - Rule quote, page 2, Fünfling: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
   - Code: `legal_actions` five-card generation and `_resolve`, `kind == "five"`.
   - Expected: the five cards enter the discard before retrieval, so the chosen card may be a pre-existing discard or one of those five components.
   - Implemented: retrieval choices are generated solely from `s.discard` before the five cards are discarded. If the discard is empty, no five-card action is legal at all.

4. **Valid combinations using Defuses or hand-held Kittens are prohibited**

   - Canonical facts: `PAIR-01`, `TRI-01`, `FIVE-01`, `FIVE-02`
   - Evidence type: `rule_quote`
   - Rule quotes, page 2:
     - Pärchen: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden …”
     - Fünfling: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst …”
     - Fünfling/Kittens: “eine beliebige Karte aus dem Ablagestapel nehmen.”
   - Code: `legal_actions`, conditions `c not in (EK, DEFUSE)` and `set(h) - {EK, DEFUSE}`.
   - Expected: any same-title pair/triple is eligible, and any five distinct titles are eligible. Under `FIVE-02`, a Kitten retrieved into a hand may participate in same-title combinations.
   - Implemented: both `EK` and `DEFUSE` are categorically excluded from every combination.

5. **A triple’s requested title is chosen after the NÖ! window and leaks the target’s hand**

   - Canonical facts: `TRI-01`, `TRI-02`, `NOPE-06`, `SET-08`
   - Evidence type: `human_decision`
   - Rule quotes:
     - Page 2, Drilling: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
     - Page 2, Drilling: “Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine solche Karte, hast du Pech gehabt.”
     - Page 1, setup: “Halte dein Blatt stets verdeckt.”
   - Approved decision in `NOPE-06`: the complete proposed action, including requested title, is announced before the NÖ!/DOCH! window.
   - Code: triple action creation, `_reaction(("triple", c, target))`, and `phase == "triple"` legal actions.
   - Expected: the actor names any title before reactions; after resolution, the target transfers it if held.
   - Implemented: the requested title is absent from the pending action and selected only after reactions. The available choices enumerate `set(s.hands[s.target])`, directly revealing every title in the target’s private hand. An absent title cannot be named explicitly.

6. **A restored action can crash or deadlock when its target spent the last card as NÖ!**

   - Canonical fact: `NOPE-07`
   - Evidence type: `human_decision`
   - Rule quote, page 2, NÖ!: “Alle Karten, die ge-NÖ!-t wurden, sind raus und bleiben auf dem Ablagestapel.”
   - Approved decision: if a legal target spends its last card during the reaction chain and the action is restored, resolution completes without a transfer.
   - Code:
     - `_resolve`, `kind == "pair"` calls `rng.choice(s.hands[target])`.
     - `_resolve`, Favor sets `phase = "favor"`.
     - `legal_actions`, Favor phase only offers cards actually held.
   - Expected: the restored pair or Favor resolves without transferring a card.
   - Implemented: a restored pair calls `random.choice` on an empty list and crashes. A restored Favor enters a phase with no legal actions and deadlocks.

7. **Shuffle leaves obsolete future-card knowledge marked as current**

   - Canonical fact: `FUT-03`
   - Evidence type: `human_decision`
   - Rule quote, page 2, Mischen: “Misch den Spielstapel sorgfältig neu.”
   - Approved decision: after Shuffle changes the order, an earlier preview is stale and must not be presented as current top-card knowledge.
   - Code: `_resolve`, `card == SHUFFLE` and `card == SEE`.
   - Expected: shuffling invalidates stored preview knowledge.
   - Implemented: Shuffle changes `s.deck` but never clears `s.seen`, so the state retains obsolete top-card information.

### Critical

None.

### Minor

None separate from the material findings above.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Correct 7+Defuse hands, Kitten count, and two-player Defuse variant |
| Ordinary turn flow | Covered | Zero-or-more plays followed by draw; living-player advancement works |
| Attack and Skip | Partial | Normal obligations work; Defuse incorrectly erases a remaining Attack turn |
| Explosion and elimination | Partial | Elimination/terminal result works, but hand cleanup is wrong |
| Defuse and reinsertion | Partial | Explicit position and single reinsertion work |
| Favor and random pair theft | Partial | Normal transfers work; restored empty-target cases fail |
| Triple | Incorrect | Request timing, absent-title choice, and information privacy are wrong |
| Five-card combination | Incorrect | Self-retrieval and card-title eligibility are incomplete |
| NÖ!/DOCH! | Partial | Toggle and discard behavior work; empty-target restoration fails |
| See the Future / Shuffle | Partial | Preview order works; Shuffle does not invalidate it |
| Terminal state and returns | Covered | Immediate sole-survivor terminal state and `+1/-1` returns |
| Private information | Partial | Hands are structurally separate, but triple choices expose target titles |

## Missing deterministic scenarios

- Defuse the first of two Attack-owed turns and verify the same player still owes one turn.
- Eliminate a player with several cards and verify the complete hand plus Kitten enters the discard.
- Play a five-card combination against an empty discard and retrieve one component.
- Use a Defuse pair/triple and a five-card set containing Defuse.
- Retrieve Kittens into hand and exercise an allowed same-title combination.
- Announce an absent title for a triple before the NÖ! window without exposing the target’s hand.
- Restore a pair after the target spends its last card as NÖ! and verify no crash.
- Restore Favor in the same circumstance and verify no deadlock.
- Preview the deck, then Shuffle, and verify stored preview knowledge is invalidated.

## Material questions for a human

No clarification is needed to score the findings above. Exact physical NÖ! reaction priority remains intentionally non-hard-testable, and the implementation’s numerical starting responder should not be scored without an additional adjudication.

```text
score: 0.50
confidence: high
critical_issues: 0
major_issues: 7
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```