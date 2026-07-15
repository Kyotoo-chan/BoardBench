## Assessment

`score: 0.40` — `confidence: high`

The module preserves the basic play/draw loop, elimination, terminal returns, Skip, previews, shuffling, donations, and Nope chaining. However, it materially contradicts setup quantities, attacked-turn replacement, target legality, and five-card retrieval. No issue appears to prevent every game from completing, so I found no critical defect.

## Findings

### Major 1 — The card pool is incomplete

- Canonical fact ID: `SET-02`
- Evidence type: `rule_quote`
- Rule evidence:
  - Page 1, setup step 2: “Mischt die restlichen Karten sorgfältig.”
  - Page 1, cover: “SPIELMATERIAL: 56 KARTEN”
  - Page 2, Katzen-Karten: “4 JEDER ART”; the canonical page displays five Katzen-Karten categories.
- Conflicting code: `CARD_COUNTS`, used by `Game.initial_state()`.
- Expected: After setting aside four Kittens and six Defuses, all 46 remaining cards belong to the setup pool.
- Implemented: `CARD_COUNTS` contains only 34 cards and only two Katzen-Karten titles. Twelve regular cards are absent, materially changing hand composition, deck size, card frequencies, and available combinations.

### Major 2 — Player-count-specific setup is wrong

- Canonical fact IDs: `SET-04`, `SET-06`, `SET-07`
- Evidence type: `rule_quote`
- Rule evidence:
  - Page 1, setup step 4: “Nehmt jetzt von den zur Seite gelegten Exploding Kittens eine Karte weniger als Spieler teilnehmen und mischt sie in den Spielstapel.”
  - Page 1, setup step 5: “Mischt zuletzt alle übrigen Karten ‚Entschärfung‘ in den Spielstapel.”
  - Page 1, two-player variant: “Mischt nur 2 Karten ‚Entschärfung‘ in den Spielstapel und legt die übrigen in die Schachtel zurück.”
  - Page 1 cover: “SPIELER: 2–5”
- Conflicting code: `Game.__init__()` and `Game.initial_state()`, especially:
  - `if num_players not in (2, 3, 4)`
  - `kittens = 2 if self.num_players == 2 ...`
  - `[DEFUSE] * 2`
- Expected:
  - Two players: one Kitten and two additional Defuses.
  - Three players: two Kittens and all three remaining Defuses.
  - Five players: supported, with four Kittens and the one remaining Defuse.
- Implemented:
  - Two players receive two Kittens.
  - Three players receive only two additional Defuses.
  - Five-player setup raises `ValueError`.

### Major 3 — An Attack played while under Attack creates three turns

- Canonical fact ID: `ATK-02`
- Evidence type: `human_decision`
- Rule quote, page 2, Angriff: “Spielt dein Opfer dabei selbst eine Karte ‚Angriff‘ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Approved decision: An Attack played during an Attack replaces the remaining obligation; the following player owes exactly two turns.
- Conflicting code: `Game._resolve_effect()`, Attack branch:
  - `remaining = s.turns_due - 1`
  - `s.turns_due = remaining + 2`
- Expected: If a player with two owed turns immediately plays Attack, the next player owes exactly two turns.
- Implemented: With `turns_due == 2`, the next player receives three turns.

### Major 4 — Empty-handed players are offered as Favor and pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rule quotes, page 2:
  - Wunsch: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”
  - Pärchen: “... um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved decisions: Empty-handed players are not legal targets for either effect.
- Conflicting code: `Game.legal_actions()` uses `_other_alive()` for both Favor and pair actions without checking the target hand.
- Expected: Actions targeting an empty-handed player are absent from `legal_actions()`.
- Implemented: Such actions are legal; resolution then silently does nothing.

### Major 5 — Five-card retrieval excludes two explicitly permitted choices

- Canonical fact IDs: `FIVE-01`, `FIVE-02`
- Evidence types: `rule_quote`, `human_decision`
- Rule quote, page 2, Fünfling: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Approved decisions:
  - The five components enter the discard before retrieval, so one of those components may immediately be retrieved.
  - An Exploding Kitten may be retrieved and remains safely in hand.
- Conflicting code: `Game.legal_actions()`:
  - Generates retrieval choices from the pre-play `state.discard`.
  - Explicitly subtracts `{EXPLODING}`.
- Expected: Retrieval choices include the five newly discarded components and any Exploding Kitten in the resulting discard.
- Implemented: A newly discarded component is unavailable unless another copy was already discarded, and Exploding Kittens are always excluded.

### Minor 1 — Triple requests cannot name an Exploding Kitten

- Canonical fact IDs: `TRI-01`, `TRI-02`, related approved treatment in `FIVE-02`
- Conflicting code: Triple requests iterate over `CARD_COUNTS.keys() | {DEFUSE}`, which omits `EXPLODING`.
- Expected: If “eine Karte” covers every card title, a player should be able to request an Exploding Kitten.
- Implemented: The title cannot be requested. This is rare and depends on gathering a safely held Kitten, so I rate it minor rather than major.

### Questions

1. `GameState` exposes every hand and the complete ordered deck to callers. `render()` hides opponents’ hands, but there is no player-specific observation API. The approved facts acknowledge that secrecy cannot be fully verified under the minimal API. A human should decide whether omniscient engine state is acceptable or whether `SET-08`, `SET-09`, and `FUT-02` require an observation boundary.

2. The canonical facts do not individually enumerate the five illustrated Katzen-Karten titles. The missing twelve cards are clear from the 56-card total and canonical page, but their exact approved title mapping should be recorded before title-specific scenarios are hard-scored.

3. Confirm whether `TRI-01` permits requesting an Exploding Kitten. The printed wording is broad, but this exact request is not explicitly adjudicated.

## Rule-area coverage

| Rule area | Result |
|---|---|
| Setup and card population | Major contradictions |
| Basic play/pass/draw flow | Substantially correct |
| Attack and owed turns | Major contradiction |
| Skip and Defuse owed-turn handling | Correct by inspection |
| Explosion, elimination, terminal returns | Correct |
| Favor and pair targeting | Major legality defect |
| Preview and shuffle | Correct |
| Nope reactions | Broadly consistent with approved convention |
| Pair/triple combinations | Mostly correct; one rare title omission |
| Five-card combination | Major contradiction |
| Private information | Unresolved API question |

## Missing deterministic scenarios

- Verify the complete initial multiset and deck size for 2, 3, 4, and 5 players.
- Verify one Kitten for two players and `player_count - 1` for every supported count.
- Verify remaining Defuse counts separately for two and three players.
- Play Attack while owing two turns and assert that the following player owes exactly two.
- Assert that empty-handed players are absent from Favor and pair target actions.
- Play a five-card combination with an initially empty discard and retrieve one just-played component.
- Retrieve an Exploding Kitten using a five-card combination and verify that it enters the hand without exploding.
- Test an Exploding Kitten as a triple requested title if the human approves that interpretation.
- Test player-specific secrecy if an observation interface is required.

```text
score: 0.40
confidence: high
critical_issues: 0
major_issues: 5
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```