Score: **0.76**, confidence: **high**. Core setup, drawing, elimination, Defuse, terminal returns, and most card effects are represented faithfully. Two material action/transition errors remain, plus two rare combination-card issues.

## Findings

### Major 1 — Attack incorrectly multiplies an existing obligation to four turns

- Rulebook, page 2, “Angriff”: “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Approved expectation ATK-02: an Attack played during an Attack replaces the remaining obligation; the following player owes exactly two turns.
- Conflicting code: `_resolve_effect()`, `kind == ATTACK`, especially `burden = state.turns_left * 2`.
- Expected: if a player owing two turns plays Attack, the next player owes exactly two turns.
- Implemented: `turns_left == 2` produces a burden of four turns.

This materially changes a common turn transition and can strongly affect elimination and the winner.

### Major 2 — Favor and Pair allow empty-handed targets

- Rulebook, page 2, “Wunsch”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
- Rulebook, page 2, “Pärchen”: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved expectations FAV-01 and PAIR-01 explicitly adjudicate that empty-handed players are not legal targets.
- Conflicting code: `legal_actions()` constructs `targets` from all other living players without checking their hands, then uses that list for Favor, Pair, and Triple actions.
- Expected: an empty-handed player is absent from Favor and Pair target choices.
- Implemented: such targets remain legal; `_resolve_effect()` subsequently turns the action into a no-op.

The player can therefore discard valuable cards for an action the approved rules declare illegal.

### Minor 1 — An acquired Exploding Kitten can be used in a five-distinct-title combination

- Rulebook, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Approved expectation FIVE-02: a Kitten retrieved from the discard remains in hand, “cannot be played singly but may participate in same-title combinations.”
- Conflicting code: `legal_actions()` builds five-card combinations from every title in `Counter(hand)`, including `EXPLODING`.
- Expected: the approved exception permits a held Kitten in matching-title combinations, not as one distinct title in a Fünfling.
- Implemented: one held Kitten plus four other titles can form a five-card combination.

This is localized and requires the unusual prior retrieval of a Kitten.

### Minor 2 — Triple cannot request an Exploding Kitten held by the target

- Rulebook, page 2, “Drilling”: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst. Besitzt er solch eine Karte, muss er sie dir geben.”
- Approved expectations TRI-01/02 describe requesting a named card; FIVE-02 permits an Exploding Kitten to exist in a hand.
- Conflicting code: `REQUESTABLE = tuple(NORMAL_COUNTS) + (DEFUSE,)` omits `EXPLODING`; Triple legal actions enumerate only `REQUESTABLE`.
- Expected: absent an exception in the Triple rule, a player can request the named Kitten title when the target holds one.
- Implemented: no such request action exists.

This is rare and does not affect ordinary games without discard retrieval.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Setup and card counts | Conforms, including two-player Defuse variation |
| Hidden hands/deck | `render()` hides other hands and deck identities; raw state remains exposed |
| Normal turn and drawing | Conforms |
| Attack | Normal Attack works; chained Attack obligation is wrong |
| Skip under Attack | Conforms; consumes one owed turn |
| Explosion and Defuse | Conforms, including explicit reinsertion position |
| Elimination and terminal state | Conforms |
| Future and Shuffle | Conforms |
| Favor | Transfer choice is explicit; empty target legality is wrong |
| Nope reactions | Toggling and discarded cards are represented |
| Pair and Triple | Core effects work; empty Pair target and rare Kitten request issues |
| Five-card combination | Pre-existing discard choice works; Kitten component is over-permitted |
| Returns | Correct zero nonterminal and `+1/-1` terminal values |

## Missing deterministic scenarios

- A player owing two turns plays Attack; verify the next player owes exactly two, not four.
- Favor excludes every empty-handed opponent.
- Pair excludes every empty-handed opponent.
- Skip twice during a two-turn Attack obligation.
- Defuse during an Attack consumes only the current owed turn.
- Elimination during an Attack clears the eliminated player’s remaining obligation.
- Retrieve an Exploding Kitten with Fünfling, then verify its permitted combination uses.
- Triple requests an Exploding Kitten held by its target.
- Cancelled Attack leaves the original player in the same individual turn.
- Multiple Nope cards alternate cancellation and restoration.
- Five-card retrieval cannot select a component newly discarded by that same combination.
- Two-player setup contains exactly two additional deck Defuses.

## Material questions for a human

- Should direct access to `GameState.hands` and `GameState.deck` count as a private-information failure, or is privacy judged only through `render()`? The approved facts acknowledge that the minimal API cannot fully verify secret information.
- In the deterministic Nope protocol, should the original actor receive a reaction opportunity before any Nope has been played? The implementation cycles through every living player, including that actor; physical timing and priority remain explicitly unresolved.

score: 0.76
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true