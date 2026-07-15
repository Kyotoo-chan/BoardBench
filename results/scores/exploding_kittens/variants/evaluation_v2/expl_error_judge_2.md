score: 0.52  
confidence: high

The module correctly covers setup counts, normal draw flow, basic elimination and terminal returns, most named cards, Nope chains, and ordinary combinations. However, several explicit transitions are materially wrong: Attack and attacked Skip debt, mandatory Defuse, and retrieving an Exploding Kitten through a five-card combination.

## Findings

### Major 1 — A normal Attack assigns three turns instead of two

- Canonical fact ID: `ATK-01`
- Evidence type: `rule_quote`
- Rule quote, page 2, “Angriff”: “Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.”
- Conflicting code: `_resolve_pending`, `kind == ATTACK`, especially `state.turn_debt = 3` at `implementation.py:407-414`.
- Expected: The attacker’s turn ends and the next living player owes exactly two turns.
- Implemented: The next player owes three turns.

### Major 2 — An Attack played while attacked does not pass exactly two turns onward

- Canonical fact ID: `ATK-02`
- Evidence type: `human_decision`
- Rule quote, page 2, “Angriff”: “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Conflicting code: `_resolve_pending`, `if state.turn_debt > 1: state.turn_debt += 1` at `implementation.py:407-410`.
- Expected: The attacked player immediately ceases being active; the following living player owes exactly two turns, replacing the remaining obligation.
- Implemented: The attacked player remains active and their own debt increases by one.

### Major 3 — One Skip incorrectly clears every attacked turn

- Canonical fact ID: `SKIP-02`
- Evidence type: `rule_quote`
- Rule quote, page 2, “Hops!”: “Falls du „Hops!“ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal „Hops!“ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `_resolve_pending`, `kind == SKIP`, setting the next player active and `turn_debt = 1` at `implementation.py:416-420`.
- Expected: One Skip consumes exactly one owed turn. If another attacked turn remains, the same player must take it.
- Implemented: A single Skip advances to the next player and clears all outstanding debt.

### Major 4 — A player holding a Defuse may voluntarily decline it

- Canonical fact ID: `DEF-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Conflicting code: `legal_actions` always includes `defuse:decline` at `implementation.py:142-150`; `_apply_defuse` eliminates the player on that action at `implementation.py:497-513`.
- Expected: Under the approved decision, a held Defuse must be used; voluntary elimination is unavailable.
- Implemented: Declining remains legal even when the player has a Defuse.

### Major 5 — A Kitten retrieved from the discard explodes again

- Canonical fact ID: `FIVE-02`
- Evidence type: `human_decision`
- Rule quotes, pages 1–2: “Wenn du ein Exploding Kitten ziehst …” and “eine beliebige Karte aus dem Ablagestapel nehmen”.
- Conflicting code: `_resolve_pending`, `kind == "five"`, where retrieving `EXPLODING` enters `phase = "defuse"` instead of adding it to the hand at `implementation.py:453-465`.
- Expected: Taking a Kitten from the discard is not drawing it. It remains safely in hand and may participate in combinations.
- Implemented: Retrieval triggers Defuse/elimination handling; using Defuse reinserts the Kitten, while declining can eliminate the player.

### Major 6 — Empty-handed players remain legal Favor and pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rule quotes, page 2:
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Conflicting code: `legal_actions` generates targets using `_other_alive` without checking target hands at `implementation.py:159-167`.
- Expected: Empty-handed players are not legal Favor or pair targets.
- Implemented: Such actions are legal, discard the played card or pair, and then resolve as a no-op.

### Minor 1 — Triple requests cannot name an Exploding Kitten

- Canonical fact IDs: `TRI-01`, `FIVE-02`
- `REQUESTABLE_CARDS` omits `EXPLODING` at `implementation.py:28-36`, and triple actions use only that list.
- A discarded Kitten may legally be retrieved into a hand. The approved facts do not restrict requested titles, so a triple should be able to request it if the target holds one.
- This is rare and localized, so it is minor rather than major.

### Question 1 — Observer boundary is not defined

`GameState` exposes every hand and the entire deck directly, while `render` shows only the current player’s hand and only reveals a preview to its owner. `SET-08` and `FUT-02` require privacy, but the approved facts acknowledge that secrecy cannot be fully verified without player-specific observations. Human clarification is needed on whether direct state access counts as public observation.

### Question 2 — Legal behavior if retained Kittens allow deck exhaustion

After correcting `FIVE-02`, a Kitten can remain in a player’s hand rather than returning to the draw pile. In games with at least three players, this may invalidate the printed claim that the pile cannot become empty before only one player remains. `_draw` currently raises `RuntimeError` on an empty deck. The packet does not adjudicate the resulting game state.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup | Covered | Correct initial hands, Kittens, and two-player Defuse variant |
| Normal turn flow | Covered | Zero-or-more plays followed by draw |
| Attack | Failed | Both ordinary and counter-Attack debt are wrong |
| Skip | Failed under Attack | Ordinary Skip works |
| Explosion/elimination | Mixed | No-Defuse elimination works; mandatory use does not |
| Defuse reinsertion | Mostly covered | Explicit positions and relative deck order work |
| Preview/shuffle | Covered | Private preview representation and deck-only shuffle |
| Favor | Mixed | Donor selects card; empty target wrongly legal |
| Nope | Covered | Discarding, toggling, and out-of-turn reactions represented |
| Pair/triple | Mixed | Core transfers work; empty pair target and Kitten request issues |
| Five-card combination | Mixed | Components discarded before retrieval; retrieved Kitten mishandled |
| Terminal/returns | Covered | Sole survivor and `+1/-1` results are correct |
| Information model | Question | No player-specific observation API |

## Missing deterministic scenarios

- Normal Attack gives the next player exactly two turns.
- Attack during an attacked turn passes exactly two turns to the following player.
- One Skip during Attack leaves one owed turn; two Skips consume both.
- A held Defuse cannot be declined.
- Defusing during Attack leaves any further owed turn intact.
- Five-card retrieval places an Exploding Kitten safely in hand.
- Favor and pair exclude empty-handed targets.
- Triple can request an Exploding Kitten held by the target.
- Positive regression: five-card retrieval may select one of its own just-discarded components.
- Empty-deck behavior after a Kitten has been retained in hand.

## Material questions for a human

- Is direct access to `GameState.hands` and `GameState.deck` considered an information leak, or is only `render` treated as an observation?
- What happens if legal discard retrieval removes enough Kittens from circulation for the draw pile to become empty with multiple players alive?

score: 0.52
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true