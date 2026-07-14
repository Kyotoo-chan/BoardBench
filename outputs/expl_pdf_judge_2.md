## Assessment

`score: 0.58` — `confidence: high`

Most setup, turn, Attack/Skip, Defuse, Nope, elimination, terminal, and return logic matches the canonical facts. However, ordinary cat-card combinations can deterministically crash despite being advertised as legal actions. Empty-handed targets are also incorrectly legal for Favor and pairs.

## Findings

### Critical — Cat-card combinations can crash

Rulebook, page 2, “Kombinationen — Pärchen”:

> “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”

Also:

> “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”

> “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”

Conflicting code: `legal_actions()` and `_play_combo()` in [implementation.py](D:/safen/Ben_T/Studium/8.Semester/BoardBench/generation_workspaces/boardbench_expl_pdf_judge2_v6e1ftkr/implementation.py:328), particularly `action.split(":")` at line 330 and positional parsing at lines 334, 346, and 360.

Expected: Titles such as `cat:taco` must work in pairs, triples, and five-card combinations.

Implemented: The title’s colon is confused with the action-format separators. For example:

```text
combo:pair:cat:taco:target:player1
```

splits such that `_play_combo()` reads the card as `cat` and attempts to parse `target` as the player number, raising `ValueError`. Triple cat combinations fail similarly. A five-card combination containing a cat title misparses its component list and can fail while removing cards.

Because cat cards constitute a large part of the deck and combinations are their principal use, this is a common reachable crash.

### Major — Empty-handed players are legal Favor and pair targets

Rulebook, page 2, “Wunsch”:

> “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”

Rulebook, page 2, “Pärchen”:

> “…um einem Mitspieler eine zufällige Karte zu stehlen.”

The approved facts explicitly adjudicate empty-handed players as illegal targets for both actions.

Conflicting code: `_opponents()` at line 234 returns every living opponent without checking their hand. `legal_actions()` uses that result for Favor at line 113 and pairs at line 122.

Expected: No Favor or pair action targeting an empty-handed player should be legal.

Implemented: Such actions are offered. After the cards and any Nope reactions are resolved, `_resolve_effect()` at lines 392–395 or 411–415 simply does nothing when the target is empty. The actor therefore discards a Favor or pair through an action that canonical facts declare illegal.

### Question — Direct state access may expose private information

Rulebook, page 1, setup:

> “Halte dein Blatt stets verdeckt.”

The draw pile is also required to be hidden. `render()` provides an appropriately restricted decision-maker view, but `GameState.hands` and `GameState.deck` are public fields at lines 57–58.

The approved facts say private information cannot be fully verified without player-specific observations. The packet does not establish whether direct access to state fields counts as an observation/API leak, so this is a question rather than a scored defect.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and card counts | Pass | Correct deals, starting Defuses, player-count Kittens, and two-player Defuse exception |
| Normal turn flow | Pass | Zero or more plays followed by draw |
| Attack/Skip obligations | Pass | Skip consumes one owed turn; Attack replaces remaining obligation with two for the next player |
| Defuse/reinsertion | Pass | Mandatory Defuse, explicit insertion position, and owed-turn accounting |
| Favor | Major issue | Donor chooses card, but empty targets are legal |
| Nope reactions | Pass | Out-of-turn chain and parity toggling represented |
| Pair/triple/five combinations | Critical issue | Cat-title action decoding can crash |
| Shuffle/preview/chance | Pass | Preview order and shuffle scope match; exact probabilities are not hard-scored |
| Elimination/terminal result | Pass | Hand and Kitten discarded; sole survivor wins immediately |
| Returns | Pass | Nonterminal zeros and terminal `+1/-1` |
| Private information | Question | Render is restricted, but state internals are directly accessible |

## Missing deterministic scenarios

- Apply a pair of each colon-bearing cat title.
- Apply a cat triple while requesting both ordinary and cat titles.
- Apply five-card combinations with a cat title in different component positions.
- Confirm Favor and pair actions exclude empty-handed opponents.
- Confirm a cat combination that is Noped discards its components without crashing.
- Confirm Defuse and Skip each consume exactly one of two Attack-owed turns.
- Confirm elimination during an attacked turn removes the remaining obligation.
- Verify what information each player can obtain through the supported observation interface.

## Material questions for a human

- Are callers expected to treat `GameState` fields as internal, or must hands and deck order be inaccessible through every public object? The canonical facts identify the information as secret but leave the observation boundary unresolved.

```text
score: 0.58
confidence: high
critical_issues: 1
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```