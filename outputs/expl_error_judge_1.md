## Assessment

`score: 0.42` — `confidence: high`

Setup counts, ordinary drawing, elimination cleanup, terminal returns, clockwise progression, private future viewing, shuffling, Favor transfer, theft, and most Nope handling are represented. However, several explicit canonical adjudications are contradicted, including core Attack/Skip flow and mandatory Defuse use.

## Findings

### Major 1 — Attack assigns the wrong player and number of turns

- Rulebook, page 2, **Angriff**: “Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.”
- Rulebook, page 2, **Angriff under Attack**: “Spielt dein Opfer dabei selbst eine Karte ‚Angriff‘ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Conflicting code: `_resolve_pending`, lines 407–414:
  - A normal Attack sets the next player’s `turn_debt` to `3`.
  - An Attack played while attacked executes `state.turn_debt += 1` without advancing `active_player`.
- Expected:
  - Normal Attack: next living player owes exactly two turns.
  - Attack while attacked: current obligation ends; following living player owes exactly two turns.
- Implemented:
  - Normal target owes three turns.
  - An attacked player remains active and winds up owing three turns.

### Major 2 — One Skip incorrectly clears every attacked turn

- Rulebook, page 2, **Hops!**: “Falls du ‚Hops!‘ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal ‚Hops!‘ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `_resolve_pending`, lines 416–420, explicitly resets `turn_debt = 1` and advances to the next player.
- Expected: one Skip consumes only the current owed turn; the attacked player remains active for any remaining owed turn.
- Implemented: one Skip ends the entire Attack obligation.

### Major 3 — A player may decline an available Defuse

- Rulebook, page 2, **Entschärfung**: “Wenn du ein Exploding Kitten ziehst, kannst du eine ‚Entschärfung‘ ausspielen, statt zu sterben.”
- Canonical DEF-01 adjudication: when a player has a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting code:
  - `legal_actions`, line 144, always includes `"defuse:decline"`.
  - `_apply_defuse`, lines 500–514, eliminates the player after that choice.
- Expected: `defuse:decline` is legal only when no Defuse is held.
- Implemented: a player holding a Defuse can choose immediate elimination, potentially changing the winner.

### Major 4 — Five-card combinations can retrieve one of their own components

- Rulebook, page 2, **Fünfling**: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Canonical FIVE-01 adjudication: the retrieved card must already have been in the discard before the combination was played.
- Conflicting code:
  - `legal_actions`, line 182: `available = sorted(set(state.discard) | set(chosen))`.
  - `_play` discards the five components before resolution.
  - `_resolve_pending` retrieves the uppermost matching copy.
- Expected: only pre-existing discard cards are eligible, and the pre-existing copy is recovered.
- Implemented:
  - A combination remains legal even with an initially empty discard by selecting one of its own cards.
  - If the requested title existed previously but is also a component, the newly discarded component is recovered instead.

### Major 5 — A Kitten retrieved from the discard explodes

- Rulebook, page 2, **Entschärfung**: “Wenn du ein Exploding Kitten ziehst …”
- Rulebook, page 2, **Fünfling**: “… darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Canonical FIVE-02 adjudication: taking a Kitten from the discard is not drawing it; it remains safely in hand.
- Conflicting code: `_resolve_pending`, lines 461–462, changes directly to `phase = "defuse"` when the recovered card is `EXPLODING`.
- Expected: add the recovered Kitten to the actor’s hand without triggering Defuse or elimination.
- Implemented: the player must Defuse it or may be eliminated through `defuse:decline`.

### Major 6 — Empty-handed players remain legal Favor and Pair targets

- Rulebook, page 2, **Wunsch**: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”
- Rulebook, page 2, **Pärchen**: “… um einem Mitspieler eine zufällige Karte zu stehlen.”
- Canonical FAV-01 and PAIR-01 adjudications: empty-handed players are not legal targets.
- Conflicting code: `legal_actions`, lines 159–167, generates targets from `_other_alive` without checking hand contents. `_resolve_pending` then silently turns either action into a no-op if the target is empty.
- Expected: exclude empty-handed players from the target actions.
- Implemented: the player can spend and discard Favor or pair cards against an empty target.

### Minor 1 — Triple cannot request an Exploding Kitten

- Rulebook, page 2, **Drilling**: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
- Conflicting code: `REQUESTABLE_CARDS`, lines 28–37, excludes `EXPLODING`.
- Expected: under the canonical decision that a retrieved Kitten can remain in a hand, its title can be requested like another held card.
- Implemented: no triple action can name an Exploding Kitten.
- This is localized and requires the rare prior retrieval of a Kitten.

## Coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Pass | Player counts, initial hands, Kittens, and two-player Defuses match |
| Turn and draw flow | Pass | Zero or more plays followed by draw is supported |
| Attack obligations | Fail | Wrong player and three rather than two turns |
| Skip | Fail | Clears all owed turns |
| Explosion and Defuse | Fail | Voluntary death allowed despite canonical adjudication |
| Elimination and terminal result | Pass | Hand cleanup, sole survivor, and `+1/-1` returns match |
| Hidden information | Partial | `render` limits hands and preview, but raw state exposes all hands/deck |
| See the Future / Shuffle | Pass | Top three preserved; only deck order shuffled |
| Favor / Pair / Triple | Partial | Effects work, but empty targets and Kitten requests are wrong |
| Five-card combination | Fail | Own-card retrieval and retrieved-Kitten behavior contradict facts |
| Nope reactions | Pass | Cancellation toggles and discarded cards are retained |
| Empty draw pile | Question | Implementation raises an exception; canonical retrieval can remove Kittens from circulation |

## Missing deterministic scenarios

1. Normal Attack gives the next living player exactly two turns.
2. Attack during an Attack transfers exactly two turns to the following player.
3. One Skip consumes one of two owed turns; two Skips consume both.
4. A player holding Defuse has no decline action.
5. Favor and Pair actions exclude empty-handed targets.
6. A five-card combination cannot retrieve a newly discarded component.
7. Retrieval chooses a pre-existing copy when a combination component has the same title.
8. A retrieved Exploding Kitten enters the hand without a Defuse phase.
9. A triple can request an Exploding Kitten held by its target.
10. Nope cancellation preserves the pre-action Attack debt and active player.

## Material questions for a human

- After implementing canonical FIVE-02, what should happen if discard retrieval places enough Exploding Kittens into hands that the draw pile eventually becomes empty? The printed assurance that the pile never empties does not address that interaction.
- Is raw `GameState` considered an omniscient engine state, or must every public state/observation hide other hands and deck order? The approved facts acknowledge that secrecy cannot be fully tested without player-specific observations.

```text
score: 0.42
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```