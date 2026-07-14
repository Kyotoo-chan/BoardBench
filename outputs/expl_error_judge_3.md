score: 0.34  
confidence: high

The implementation models setup, ordinary draws, elimination, returns, card reactions, and most card effects coherently. However, common Attack/Skip transitions are materially wrong, and several explicit canonical adjudications are contradicted.

## Findings

### Critical

1. **Attack assigns the wrong player and number of turns**

   - Rulebook, page 2, “Angriff”: “Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.”
   - Rulebook, page 2, “Angriff”: “Spielt dein Opfer dabei selbst eine Karte ‚Angriff‘ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
   - Conflicting code: `Game._resolve_pending`, `kind == ATTACK`.
   - Expected:
     - A normal Attack advances to the next living player with exactly two owed turns.
     - An Attack played while attacked ends the current player’s obligation and gives the following player exactly two turns.
   - Implemented:
     - A normal Attack sets `turn_debt = 3`, giving the victim three turns.
     - Under Attack, it executes `state.turn_debt += 1` without advancing `active_player`, leaving the attacker active with additional debt.
   - This fundamentally changes a common turn-control card and can produce long, incorrect turn sequences.

### Major

2. **One Skip incorrectly clears every attacked turn**

   - Rulebook, page 2, “Hops!”: “Falls du ‚Hops!‘ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal ‚Hops!‘ ausspielen, um beide Züge zu beenden.”
   - Conflicting code: `Game._resolve_pending`, `kind == SKIP`.
   - Expected: one Skip consumes exactly one currently owed turn; the attacked player remains active if another turn is owed.
   - Implemented: every Skip advances to the next player and resets `turn_debt = 1`, clearing all outstanding turns.

3. **A player may decline Defuse despite the approved mandatory-use decision**

   - Rulebook, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine ‚Entschärfung‘ ausspielen, statt zu sterben.”
   - Canonical `DEF-01`: if the player possesses a Defuse, it must be used; voluntary elimination is not offered.
   - Conflicting code: `Game.legal_actions` always includes `"defuse:decline"`; `Game._apply_defuse` eliminates the player when it is selected.
   - Expected: decline is available only when no Defuse is held.
   - Implemented: a player holding one or more Defuses can deliberately die.

4. **Five-card combinations can retrieve one of their own components**

   - Rulebook, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
   - Canonical `FIVE-01`: the selected card must already have been in the discard before playing the combination.
   - Conflicting code:
     - `Game.legal_actions` computes `available = sorted(set(state.discard) | set(chosen))`.
     - `Game._play` discards the five components before resolving retrieval.
     - `Game._resolve_pending` retrieves the uppermost matching copy.
   - Expected: only pre-existing discard cards are selectable, and retrieval must remove such a copy.
   - Implemented: with an initially empty discard, the player can still choose one of the five played titles and immediately recover it. Even if an older matching copy exists, the uppermost matching copy will normally be the just-played component.

5. **Retrieving an Exploding Kitten incorrectly triggers explosion/Defuse resolution**

   - Rulebook, page 2, “Fünfling”: “...darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
   - Canonical `FIVE-02`: taking a Kitten from the discard is not drawing it; it does not explode and remains in hand.
   - Conflicting code: `Game._resolve_pending`, `kind == "five"`, sets `state.phase = "defuse"` when `recovered == EXPLODING`.
   - Expected: the recovered Kitten enters the actor’s hand without explosion.
   - Implemented: it enters no hand and initiates the Defuse/elimination phase, potentially consuming a Defuse or killing the player.

6. **Empty-handed players remain legal Favor and Pair targets**

   - Rulebook, page 2, “Wunsch”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”
   - Rulebook, page 2, “Pärchen”: “...um einem Mitspieler eine zufällige Karte zu stehlen.”
   - Canonical `FAV-01` and `PAIR-01`: empty-handed players are not legal targets.
   - Conflicting code: `Game.legal_actions` uses `_other_alive(...)` without filtering by hand contents for both Favor and Pair.
   - Expected: only living opponents with at least one card are offered as targets.
   - Implemented: empty opponents are legal targets; resolution silently has no effect.

7. **A held Exploding Kitten cannot be requested with a Triple**

   - Rulebook, page 2, “Drilling”: “...dass du dir eine Karte von dem Mitspieler wünschen darfst. Besitzt er solch eine Karte, muss er sie dir geben.”
   - Canonical `FIVE-02`: an Exploding Kitten retrieved from the discard remains in hand.
   - Conflicting code: `REQUESTABLE_CARDS` excludes `EXPLODING`; Triple actions iterate only over that tuple.
   - Expected: a player may request any title that an opponent can hold, including a safely retrieved Exploding Kitten.
   - Implemented: no Triple action can request that title.

### Minor

None identified.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Pass | Correct dealing, starting Defuses, Kittens, and two-player Defuse variant |
| Normal turn flow | Pass | Zero-or-more plays followed by draw is represented |
| Attack | Fail | Wrong player/debt transitions |
| Skip | Fail | Clears all attacked turns |
| Explosion/Defuse | Fail | Voluntary death allowed while holding Defuse |
| Elimination/terminal | Pass | Hand and Kitten discarded; sole survivor and returns are correct |
| See the Future | Pass | Top three/all remaining shown without reordering |
| Shuffle | Pass | Only draw-pile order changes |
| Favor | Partial | Donation choice is explicit; empty targets are legal |
| Nope | Pass | Out-of-turn toggle chain and discarded cancelled cards represented |
| Pair/Triple | Partial | Core transfers work; target/request domains are incomplete |
| Five-card combination | Fail | Own-card retrieval and Kitten handling contradict canonical decisions |
| Private information | Partial | Rendering is player-specific, but full state exposes hidden data; canonical facts say this is not fully hard-testable |

## Missing deterministic scenarios

- Normal Attack gives the next player exactly two turns.
- Attack played during an attacked turn transfers exactly two turns to the following player.
- One Skip under Attack consumes one owed turn; two Skips consume both.
- A player holding Defuse has no decline action.
- A player without Defuse is eliminated after drawing a Kitten.
- Five distinct titles cannot retrieve a component when the prior discard is empty.
- Five-card retrieval with a matching played title removes the pre-existing discard copy.
- A retrieved Exploding Kitten enters the hand without Defuse or elimination.
- Favor and Pair exclude empty-handed opponents.
- A Triple can request an Exploding Kitten held after discard retrieval.
- Defusing the first of two attacked turns leaves the second turn owed.
- Elimination during an attacked turn removes the remaining debt.

## Material questions for a human

None. The canonical facts resolve the material discrepancies above.

score: 0.34
confidence: high
critical_issues: 1
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true