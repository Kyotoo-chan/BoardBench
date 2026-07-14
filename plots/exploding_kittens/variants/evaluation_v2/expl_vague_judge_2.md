score: 0.68  
confidence: high

The module covers most setup, ordinary turn flow, named-card effects, reactions, elimination, and returns coherently. Three material legal/transition errors remain: Attack stacking multiplies obligations, five-card retrieval excludes newly discarded components, and empty-handed theft/Favor targets remain legal.

## Findings

### Major — Attack can impose four turns instead of exactly two

- Canonical fact: `ATK-02`
- Evidence type: `human_decision`
- Rule quote: “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.” — page 2, “Angriff”
- Conflicting code: `Game._resolve_effect`, `kind == ATTACK`
- Expected: An Attack played while resolving an Attack replaces the remaining obligation; the following player owes exactly two turns.
- Implemented: `burden = state.turns_left * 2`. Playing Attack on the first of two owed turns assigns four turns to the next player.
- Impact: A common card interaction materially changes turn count and exposure to draws.

### Major — Five-card combinations cannot retrieve a newly discarded component

- Canonical fact: `FIVE-01`
- Evidence type: `rule_quote`
- Rule quote: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” — page 2, “Fünfling”
- Conflicting code: `Game.legal_actions`, `available_discard`; five-combination construction
- Expected: The five cards enter the discard before retrieval. The player may retrieve any card then present, including one of those five components.
- Implemented: Retrieval choices come exclusively from `state.discard` before the five components are discarded. A combination is not offered at all when the discard was previously empty, and a newly introduced component title cannot be selected.
- Impact: A specifically approved combination outcome is absent.

### Major — Empty-handed players are legal Favor and pair targets

- Canonical facts: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rule quotes:
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.” — page 2, “Wunsch”
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.” — page 2, “Pärchen”
- Conflicting code: `Game.legal_actions`, construction of `targets`
- Expected: Empty-handed players are not legal targets for Favor or pair theft.
- Implemented: `targets` contains every other living player regardless of hand size. Resolution then silently produces no transfer when that target is empty.
- Impact: Illegal actions can waste cards while appearing valid, materially changing action legality and player decisions.

### Minor — A retrieved Exploding Kitten cannot be requested by a triple

- Canonical facts: `TRI-01`, `FIVE-02`
- Evidence:
  - “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.” — page 2, “Drilling”
  - Approved human decision: a Kitten retrieved from the discard remains in hand and may participate in same-title combinations.
- Conflicting code: `REQUESTABLE`, which omits `EXPLODING`
- Expected: The broad named-card request appears to include an Exploding Kitten legitimately held after discard retrieval.
- Implemented: Triple request actions can name normal cards or Defuse, but never Exploding Kitten.
- Impact: Rare and localized. If the intended scope of “eine Karte” excludes Kittens, this should instead be treated as a clarification.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Correct starting hands, Kitten count, and two-player Defuse rule |
| Normal turn flow | Covered | Zero or more plays followed by draw |
| Attack and owed turns | Contradicted | Normal Attack works; Attack-on-Attack can produce four turns |
| Skip and Defuse under Attack | Covered | Each consumes one owed turn |
| Explosion and elimination | Covered | Hand and Kitten discarded; remaining obligations disappear |
| Terminal result and returns | Covered | Immediate sole-survivor win; correct `+1/-1` returns |
| Future and Shuffle | Covered | Private preview and order-only shuffle represented |
| Favor and pair | Partial | Transfer logic works, but empty targets are legal |
| Triple | Partial | Ordinary requests work; Kitten title omitted |
| Five-card combination | Contradicted | Cannot retrieve newly discarded components |
| Nope reactions | Covered | Out-of-turn chain, toggling, and discarded cancelled cards |
| Private information | Partial/limited | Rendering hides other hands, though raw state remains inspectable |

## Missing deterministic scenarios

- Play Attack during the first of two owed turns; assert that the next player owes exactly two turns.
- Play a five-card combination with an initially empty discard and retrieve one component.
- Play five distinct titles where one component title was absent from the prior discard; retrieve that component.
- Verify that an empty-handed player is absent from Favor targets.
- Verify that an empty-handed player is absent from pair targets.
- Retrieve an Exploding Kitten, construct a supported triple state, and test whether it can be requested.
- Exercise Attack followed by Defuse, Skip, and elimination separately to guard the approved obligation rules.

## Material questions for a human

- Does a triple’s request for “eine Karte” include an Exploding Kitten held through five-card discard retrieval? The approved facts permit such Kittens in hand and in same-title combinations, but do not explicitly adjudicate triple request vocabulary.
- Is raw `GameState` access acceptable for the privacy requirement, or must the API expose player-specific observations? The packet says secret information cannot be fully verified through the minimal API, so this was not scored as a contradiction.

score: 0.68
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true