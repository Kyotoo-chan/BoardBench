score: 0.48, confidence: high. Core turn, elimination, terminal-return, and most named-card mechanics are represented, but setup is materially wrong for multiple supported player counts, attacked turns stack incorrectly, and five-card retrieval omits explicitly approved choices.

## Findings

### Major 1 — Two-player setup inserts an extra Exploding Kitten

- Canonical fact ID: `SET-04`
- Evidence type: `rule_quote`
- Rule evidence: “Nehmt jetzt von den zur Seite gelegten Exploding Kittens eine Karte weniger als Spieler teilnehmen und mischt sie in den Spielstapel.” — page 1, `SPIELAUFBAU`, step 4.
- Conflicting code: `initial_state()`, `kittens = 2 if self.num_players == 2 else self.num_players - 1` (line 75).
- Expected: two players receive exactly one Kitten in the draw pile.
- Implemented: two Kittens are inserted.

This materially changes the default two-player game’s deck composition and risk.

### Major 2 — Defuse setup and player-count support are wrong

- Canonical fact IDs: `SET-06`, `SET-07`
- Evidence type: `rule_quote`
- Rule evidence:
  - “Mischt zuletzt alle übrigen Karten ‚Entschärfung‘ in den Spielstapel.” — page 1, `SPIELAUFBAU`, step 5.
  - “Mischt nur 2 Karten ‚Entschärfung‘ in den Spielstapel und legt die übrigen in die Schachtel zurück.” — page 1, `VARIANTE FÜR ZWEI SPIELER`.
  - “SPIELER: 2–5” — page 1, cover.
- Conflicting code:
  - `Game.__init__()` rejects five players (lines 58–59).
  - `initial_state()` always adds `[DEFUSE] * 2` (line 76).
- Expected:
  - 2 players: two additional Defuses.
  - 3 players: three remaining Defuses.
  - 4 players: two remaining Defuses.
  - 5 players: one remaining Defuse, and five-player games must be constructible.
- Implemented:
  - 2, 3, and 4 players always receive two deck Defuses.
  - 5 players are rejected.

The four-player Defuse count happens to be correct, but three- and five-player setup are not.

### Major 3 — An Attack played while attacked creates three owed turns

- Canonical fact ID: `ATK-02`
- Evidence type: `human_decision`
- Rule evidence: “Spielt dein Opfer dabei selbst eine Karte ‚Angriff‘ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.” — page 2, `ANGRIFF`.
- Conflicting transition: `_resolve_effect()`, `remaining = s.turns_due - 1` followed by `s.turns_due = remaining + 2` (lines 276–279).
- Expected: under the approved adjudication, the new Attack replaces the remaining obligation; the following player owes exactly two turns.
- Implemented: if the victim attacks during the first of two owed turns, the following player owes `1 + 2 = 3` turns.

### Major 4 — Five-card retrieval excludes valid choices

- Canonical fact IDs: `FIVE-01`, `FIVE-02`
- Evidence type: `human_decision`
- Rule evidence: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” — page 2, `FÜNFLING`.
- Conflicting code: `legal_actions()` builds retrieval choices from `set(state.discard) - {EXPLODING}` before the five components are discarded (lines 136–141).
- Expected:
  - The five components enter the discard before retrieval.
  - Any of those just-discarded components may therefore be retrieved.
  - An Exploding Kitten already in the discard may be retrieved and held without exploding.
- Implemented:
  - A component absent from the discard before the combination cannot be retrieved.
  - Exploding Kitten is categorically excluded.

### Minor 1 — Empty-handed players remain legal Favor and pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Conflicting code: `legal_actions()` enumerates every other living player without checking their hand (lines 121–127).
- Expected: approved facts declare empty-handed players illegal targets.
- Implemented: the play is accepted and later resolves without a transfer.

This is localized but exposes actions that should not be legal.

### Minor 2 — Exploding Kitten cannot be requested by a triple

- Canonical fact IDs: `TRI-01`, `TRI-02`, `FIVE-02`
- Conflicting code: triple requests are limited to `CARD_COUNTS.keys() | {DEFUSE}` (line 131), which omits `EXPLODING`.
- Expected: once a player legally holds a discarded Kitten, a triple may request that title; transfer occurs if the target has it.
- Implemented: no such request action is exposed.

### Question — The implemented card inventory totals only 44 cards

`CARD_COUNTS` provides 34 ordinary cards; adding six Defuses and four Kittens yields 44, although the canonical cover states “SPIELMATERIAL: 56 KARTEN.” The `KATZEN-KARTEN — 4 JEDER ART` panel visually presents more cat-card types than the two encoded by `ZOMBIE` and `EYE`.

The approved facts do not provide a fact ID enumerating all five cat-card titles, so I have not scored this as a contradiction. It should be adjudicated and converted into an explicit inventory fact because the missing cards substantially alter deck size and card frequencies.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup | Incorrect | Wrong 2-player Kittens, wrong 3-player Defuses, no 5-player support |
| Turn flow | Mostly correct | Zero-or-more plays and turn-ending draw represented |
| Attack/Skip obligations | Incorrect | Skip consumption works; Attack-on-Attack stacks incorrectly |
| Draw, explosion, Defuse | Correct | Mandatory Defuse, explicit insertion choice, and owed-turn continuation represented |
| Elimination/terminal | Correct | Hand and Kitten discarded; sole survivor wins; returns are `+1/-1` |
| Future/Shuffle | Correct | Private top-three record and deck-only shuffle represented |
| Favor | Minor deviation | Donation choice explicit; empty target wrongly legal |
| Nope reactions | Mostly correct | Out-of-turn toggle window and discarded cancelled cards represented |
| Pair/triple | Mostly correct | Random pair theft and named triple request; target/request edge cases remain |
| Five-card combination | Incorrect | Cannot retrieve a new component or discarded Kitten |
| Hidden information | Partially covered | `render()` hides other hands, though raw state remains globally inspectable |

## Missing deterministic scenarios

- Two-player setup contains exactly one Kitten and two additional Defuses.
- Three-player setup contains two Kittens and three additional Defuses.
- Five-player construction succeeds with four Kittens and one additional Defuse.
- Attack during the first attacked turn leaves the following player exactly two turns.
- Five distinct cards can retrieve one of their own newly discarded components.
- A five-card combination can retrieve an Exploding Kitten without triggering an explosion.
- Empty-handed players are absent from Favor and pair target actions.
- A triple can request an Exploding Kitten held by its target.
- Full 56-card inventory accounting once the missing cat-title inventory is approved.

## Material questions for a human

- Please add an approved fact enumerating all cat-card titles and quantities. The canonical materials indicate 56 cards, while the implementation accounts for only 44.
- Should direct inspection of `GameState.hands`, `deck`, and `known_top` be treated as an information leak, or is secrecy evaluated only through player-specific rendering/observations? The current approved facts leave full verification unresolved.

score: 0.48
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true