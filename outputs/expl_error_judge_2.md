score: 0.40  
confidence: high

The basic game loop is functional, but six explicit rule contradictions materially affect turn counts, legal actions, elimination, and card retrieval. Setup, ordinary drawing, shuffling, peeking, terminal detection, and returns are substantially aligned.

## Findings

### Major 1 — Attack assigns the wrong number of turns and chains incorrectly

- Rulebook, page 2, “Angriff”: “Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.”
- Rulebook, page 2: “Spielt dein Opfer dabei selbst eine Karte ‚Angriff‘ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Conflicting code: `_resolve_pending()`, `kind == ATTACK`, especially `state.turn_debt = 3` and `state.turn_debt += 1`.
- Expected: A normal Attack advances to the next living player with exactly two owed turns. An Attack played while attacked immediately ends that player’s obligation and advances to the following player, who owes exactly two turns.
- Implemented: A normal Attack creates three turns. During an attacked turn, playing Attack leaves the same player active and increases their debt instead of advancing play.

This substantially changes draw exposure and therefore eliminations and the winner.

### Major 2 — One Skip cancels every outstanding attacked turn

- Rulebook, page 2, “Hops!”: “Falls du ‚Hops!‘ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal ‚Hops!‘ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `_resolve_pending()`, `kind == SKIP`, which unconditionally sets the next player active and resets `turn_debt = 1`.
- Expected: One Skip consumes exactly one owed turn. If another attacked turn remains, the same player continues with it.
- Implemented: One Skip advances to the next player and clears all outstanding debt.

### Major 3 — A player may voluntarily decline an available Defuse

- Rulebook, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine ‚Entschärfung‘ ausspielen, statt zu sterben.”
- Approved DEF-01 adjudication: if the player possesses a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting code: `legal_actions()` always exposes `"defuse:decline"` in the `defuse` phase; `_apply_defuse()` eliminates the player when that action is selected.
- Expected: Decline is available only when no Defuse exists—or elimination should occur automatically in that case. A player holding Defuse must choose a reinsertion position.
- Implemented: A player holding one or more Defuses may deliberately die, potentially deciding the winner.

### Major 4 — Five-card combinations may retrieve their own newly discarded components

- Rulebook, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Approved FIVE-01 adjudication: the selected card must already have been in the discard before playing the combination.
- Conflicting code:
  - `legal_actions()` calculates availability as `set(state.discard) | set(chosen)`.
  - `_play()` discards the five chosen cards before resolution.
  - `_resolve_pending()` retrieves the uppermost matching copy, which can be a just-played component.
- Expected: Retrieval choices come solely from the pre-existing discard, and resolution must remove such a pre-existing card.
- Implemented: A five-card combination can retrieve one of its own components, even when the discard was previously empty. If a matching title existed earlier, the reverse search can still select the newly discarded copy instead.

### Major 5 — Retrieving a discarded Kitten incorrectly triggers an explosion

- Rulebook, page 2, “Fünfling”: “... darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Rulebook, page 2, “Exploding Kitten”: “Wenn du ein Exploding Kitten ziehst ...”
- Approved FIVE-02 adjudication: taking a Kitten from the discard is not drawing it from the draw pile; it enters the player’s hand without exploding.
- Conflicting code: `_resolve_pending()`, `kind == "five"`, branches on `recovered == EXPLODING` and sets `state.phase = "defuse"` instead of adding the card to the hand.
- Expected: The retrieved Kitten enters the actor’s hand. It neither explodes nor requires Defuse.
- Implemented: Retrieval initiates the explosion/Defuse procedure and may eliminate the player or reinsert the Kitten into the deck.

### Major 6 — Empty-handed players remain legal Favor and Pair targets

- Rulebook, page 2, “Wunsch”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”
- Rulebook, page 2, “Pärchen”: “... um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved FAV-01 and PAIR-01 adjudications: empty-handed players are not legal targets.
- Conflicting code: `legal_actions()` generates Favor and Pair actions for every result of `_other_alive()` without checking the target’s hand. `_resolve_pending()` then silently makes either effect a no-op when the target is empty.
- Expected: Empty-handed players must be omitted from the legal targets.
- Implemented: Players can discard a Favor or pair while selecting an invalid target and receive nothing.

### Minor 1 — Exploding Kitten is excluded from Triple requests

- `REQUESTABLE_CARDS` omits `EXPLODING`.
- Approved FIVE-02 permits a retrieved Kitten to remain in a hand, while TRI-01 permits requesting a named card.
- Consequently, after the five-card retrieval defect is corrected, a player holding a Kitten cannot be asked for it through a Triple. This is rare and does not independently break the ordinary game loop.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Player count and setup | Aligned |
| Initial hands and Defuse counts | Aligned |
| Hidden shuffled draw pile | Aligned |
| Zero-or-more plays before drawing | Aligned |
| Normal draw and clockwise advance | Aligned |
| Attack | Major contradiction |
| Skip | Major contradiction under Attack |
| Defuse and reinsertion | Position choice aligned; mandatory use contradicted |
| Favor | Resolution aligned for nonempty targets; legality defect |
| Pair | Random transfer aligned for nonempty targets; legality defect |
| Triple | Generally aligned; request-title omission |
| Five-card combination | Major eligibility and Kitten-resolution defects |
| Nope reactions | Broadly aligned with approved deterministic convention |
| See the Future | Aligned, including fewer than three cards |
| Shuffle | Aligned |
| Elimination and discard | Aligned once elimination is valid |
| Terminal condition | Aligned |
| Returns | Aligned: winner `+1`, eliminated players `-1` |
| Private information | Render limits hands/peek to current viewer; full secrecy remains API-limited |

## Missing deterministic scenarios

Recommended scenarios should establish:

1. A normal Attack gives the next player exactly two turns.
2. Attack played during an attacked turn advances immediately and replaces the remaining obligation with exactly two turns.
3. One Skip under Attack consumes only one owed turn.
4. Two Skips consume both attacked turns.
5. A player holding Defuse has no decline action.
6. A player lacking Defuse is eliminated with hand and Kitten discarded.
7. Five distinct titles cannot retrieve a component when the prior discard is empty.
8. A five-card retrieval selects a pre-existing discard copy when the same title is among the five components.
9. Retrieving a Kitten places it in hand without entering the Defuse phase.
10. Empty-handed players are absent from Favor and Pair target actions.
11. A cancelled Attack leaves the original player’s turn and debt unchanged.
12. A Defuse during an attacked turn ends only the current owed turn.

## Material questions for a human

No additional rulebook clarification is required for the major findings; the approved facts decide them. One low-frequency interface point could be confirmed: whether `EXPLODING` must be included among Triple request titles once a Kitten has entered a hand through five-card retrieval.

```text
score: 0.40
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```