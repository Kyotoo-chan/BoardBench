score: 0.58  
confidence: high

The setup, ordinary turn flow, Attack obligations, Defuse handling, elimination, terminal returns, privacy-oriented rendering, and Nope toggling are substantially represented. However, a common family of explicitly legal combination actions can crash, and two material legality rules are incomplete.

## Findings

### Critical — Cat-card combinations exposed as legal actions crash

- Canonical facts: `PAIR-01`, `TRI-01`, `FIVE-01`
- Evidence type: `rule_quote`
- Page/section: page 2, “Kombinationen”
- Exact quotes:
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
  - “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
  - “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Conflicting symbols/transitions:
  - `CAT_CARDS`
  - `GameState.legal_actions()`
  - `GameState._play_combo()`, especially `parts = action.split(":")` and `parts[2]`
- Expected: A legal pair, triple, or five-card combination containing a cat-card title must resolve normally.
- Implemented: Cat titles themselves contain `:`, such as `cat:taco`, but `_play_combo()` also uses colons as structural delimiters. Consequently:
  - a cat pair/triple fails while parsing the target;
  - a five-card combination containing a cat is split into nonexistent card names and can fail after already discarding earlier components, leaving partially mutated state.
- Severity rationale: The module advertises these actions as legal and then raises an exception on execution. Cat cards constitute the principal dedicated combination cards, making this a common crash path.

### Major — Five-card retrieval omits newly discarded components unless that title was already discarded

- Canonical fact: `FIVE-01`
- Evidence type: `human_decision`
- Page/section: page 2, “Kombinationen – Fünfling”
- Exact quote: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Conflicting symbols:
  - `GameState.legal_actions()`
  - `if len(distinct) >= 5 and self.discard`
  - `retrievable = sorted(set(self.discard))`
- Expected: The five components enter the discard before retrieval. Therefore, the player may retrieve one of those components, including when the discard was previously empty.
- Implemented: Retrieval choices are calculated only from the pre-action discard. No five-card action exists when the discard is empty, and a newly discarded component is selectable only if another copy of its title was already present.
- Impact: A material combination option expressly permitted by the corrected approved fact is absent.

### Major — Empty-handed players remain legal Favor and pair targets

- Canonical facts: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Page/section: page 2, “Wunsch” and “Kombinationen – Pärchen”
- Exact quotes:
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Conflicting symbols/transitions:
  - `GameState._opponents()`
  - Favor and pair generation in `GameState.legal_actions()`
  - empty-target fallbacks in `_resolve_effect()`
- Expected: Per the approved facts, empty-handed players are not legal Favor or pair targets.
- Implemented: `_opponents()` filters only for living players. It generates Favor and pair actions against empty-handed targets; resolution then silently produces no transfer.
- Impact: Players can legally spend and discard cards on targets that the approved action space excludes.

### Question — Deck exhaustion after retrieving Kittens

- Relevant facts: `FIVE-01`, `FIVE-02`
- Page 1 says: “Keine Sorge, der Spielstapel wird nie leer, weil alle Spieler (außer einem) vorher Exploding Kittens ziehen werden – Explosionen garantiert!”
- The approved adjudication nevertheless permits retrieving an Exploding Kitten into a hand, potentially removing enough Kittens from circulation that the deck can empty with multiple survivors.
- `GameState._draw()` raises `RuntimeError` on an empty deck.
- The packet does not define the result of this adjudication-created state. This requires a human rule/API decision and should not presently be scored as a contradiction.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup | Covered | Correct dealing, starting Defuses, Kittens, and two-player Defuse variant |
| Normal turn flow | Covered | Zero or more plays followed by draw |
| Attack/Skip obligations | Covered | Skip consumes one owed turn; Attack replaces obligation with two for next player |
| Draw/Defuse/elimination | Covered | Mandatory Defuse, explicit reinsertion, discard, elimination, and owed-turn handling |
| Named card effects | Mostly covered | Favor has invalid empty targets |
| Nope reactions | Covered | Out-of-turn chain and alternating cancellation are represented |
| Combinations | Defective | Cat-title parsing crash, incomplete five-card retrieval, invalid pair targets |
| Private information | Mostly covered | Render hides hands/deck and limits preview to its actor |
| Terminal/returns | Covered | Sole survivor and `+1/-1` returns |
| Exceptional deck exhaustion | Undecided | Approved facts do not specify the resulting behavior |

## Missing deterministic scenarios

- Execute a pair using each `cat:*` title and verify no parsing exception.
- Execute a triple using a `cat:*` title, including requesting another colon-containing cat title.
- Execute a five-card combination containing one or more cat titles and verify atomic state transition.
- With an initially empty discard, play five distinct titles and retrieve one of those five components.
- Retrieve a newly discarded component whose title had no prior discard copy.
- Verify empty-handed players are absent from Favor and pair target actions.
- Verify a failed/invalid action cannot partially discard combination components.
- Retrieve all available Kittens from the discard and exercise eventual deck exhaustion after a human outcome is approved.

## Material questions for a human

1. What terminal or continuation behavior should apply if five-card retrieval removes enough Kittens that the draw pile empties with multiple living players?
2. Should implementations explicitly prevent that state, or should BoardBench define an API result for empty-deck exhaustion?

score: 0.58
confidence: high
critical_issues: 1
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true