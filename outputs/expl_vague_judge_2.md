score: 0.70, confidence: high. Setup, ordinary turn flow, Defuse, elimination, terminal results, returns, and most named-card effects are faithful. The main defects are incorrect chained-Attack arithmetic and illegal empty-handed targets.

## Findings

### Major — Chained Attack can impose four turns instead of two

- Rulebook, page 2, “Angriff”: “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Approved ATK-02 adjudication: an Attack played during an Attack replaces the remaining obligation; the following player owes exactly two turns.
- Conflicting code: `Game._resolve_effect`, `kind == ATTACK`, particularly `burden = state.turns_left * 2` at `implementation.py:444`.
- Expected: if a player owing two turns plays Attack, their obligation ends and the next living player owes exactly two turns.
- Implemented: when `turns_left == 2`, the next player receives four turns. This materially changes turn flow and explosion exposure.

### Major — Empty-handed players are offered as Favor and pair targets

- Rulebook, page 2, “Wunsch”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
- Rulebook, page 2, “Pärchen”: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved FAV-01 and PAIR-01 expectations explicitly make empty-handed players illegal targets.
- Conflicting code: `Game.legal_actions`, `targets` at `implementation.py:167`, Favor generation at `implementation.py:181`, and pair generation at `implementation.py:190`. Targets are filtered only by life status. `_resolve_effect` at `implementation.py:450` and `implementation.py:456` then silently does nothing if the selected hand is empty.
- Expected: these actions must not be legal against an empty-handed player.
- Implemented: the player may spend and discard the Favor or pair for a guaranteed no-op. The same target list also permits an empty target for triples, despite the triple being described as “Wie ein Pärchen.”

### Minor — Exploding Kitten cannot be named in a triple request

`REQUESTABLE` at `implementation.py:40` excludes `EXPLODING`, so triple actions cannot request that title. Under approved FIVE-01/FIVE-02, a retrieved Kitten can legally remain in a hand and participate in same-title combinations. The rulebook’s triple instruction permits requesting a card from the target, without excluding that title. This matters only after the rare discard-retrieval path.

### Question — No defined transition if the draw pile actually becomes empty

Page 1, “Spielende,” states: “Keine Sorge, der Spielstapel wird nie leer, weil alle Spieler (außer einem) vorher Exploding Kittens ziehen werden – Explosionen garantiert!”

However, approved FIVE-01/FIVE-02 permits Kittens to be removed from the discard pile and held without exploding. In sufficiently constructed play this may undermine the rulebook’s invariant. `Game._draw` raises `RuntimeError` at `implementation.py:477` rather than defining a game transition. The packet does not establish what the result should be if all remaining Kittens are held and the deck is depleted, so this is a clarification question rather than a scored contradiction.

## Rule-area coverage

| Rule area | Result |
|---|---|
| Setup and card counts | Aligned |
| Private hands and hidden deck | Represented; full secrecy not externally verifiable |
| Zero-or-more plays, then draw | Aligned |
| Skip and owed turns | Aligned |
| Attack | Major chained-Attack error |
| Explosion, Defuse, reinsertion | Aligned |
| Elimination and terminal winner | Aligned |
| Favor and pair targeting | Major legality error |
| Future and Shuffle | Aligned |
| Nope reaction chain | Aligned with approved deterministic convention |
| Pair/triple/five combinations | Mostly aligned; rare triple-title omission |
| Returns | Correct `0`, then winner `+1` and eliminated players `-1` |

## Missing deterministic scenarios

- An attacked player plays Attack while still owing two turns; the next player must owe exactly two.
- Favor and pair actions are absent when every possible target has an empty hand.
- A triple against an empty-handed target is rejected.
- A retrieved Exploding Kitten can be requested or used in a same-title combination without exploding.
- Defusing during the first of two owed turns leaves exactly one owed turn.
- Odd and even Nope chains around Favor and combinations.
- Deck depletion after Kittens have been retrieved into hands.
- Future knowledge is visible only to the acting player and is cleared after draw or shuffle.

## Material questions for a human

- What transition or terminal result applies if discard retrieval allows the draw pile to become empty while multiple players remain?
- Should the approved “named card” interpretation for triples explicitly include an Exploding Kitten held after discard retrieval?

```text
score: 0.70
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```