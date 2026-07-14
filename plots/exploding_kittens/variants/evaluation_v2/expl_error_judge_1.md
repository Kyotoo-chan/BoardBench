score: 0.42  
confidence: high

The basic setup, normal draw flow, reactions, ordinary card effects, elimination, and terminal returns are largely represented. However, Attack and Skip obligations are materially wrong, voluntary elimination is illegally offered, and Exploding Kittens retrieved through a five-card combination are resolved incorrectly.

## Findings

### Major

1. Attack assigns the wrong player and number of turns

- Canonical facts: `ATK-01`, `ATK-02`
- Evidence type: `human_decision`
- Rule quote, page 2, “Angriff”: “Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.” Also: “Spielt dein Opfer dabei selbst eine Karte ‚Angriff‘ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Conflicting code: `Game._resolve_pending`, `kind == ATTACK`, especially `turn_debt = 3` and `turn_debt += 1` at lines 407–414.
- Expected: A normal Attack gives the next living player exactly two turns. Under Attack, a counter-Attack ends the current attacked player’s obligation and gives the following player exactly two turns.
- Implemented: A normal Attack assigns three turns. An Attack played while owing turns increases debt and leaves the attacker active, instead of transferring exactly two turns to the following player.

2. One Skip incorrectly removes every outstanding attacked turn

- Canonical fact: `SKIP-02`
- Evidence type: `rule_quote`
- Rule quote, page 2, “Hops!”: “Falls du ‚Hops!‘ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal ‚Hops!‘ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `Game._resolve_pending`, `kind == SKIP`, lines 416–420.
- Expected: One Skip consumes exactly one owed turn; if another attacked turn remains, the same player continues.
- Implemented: Skip always advances to the next living player and resets `turn_debt` to one, cancelling all outstanding attacked turns.

3. A player holding a Defuse may illegally decline it and die

- Canonical fact: `DEF-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine ‚Entschärfung‘ ausspielen, statt zu sterben.”
- Conflicting code: `Game.legal_actions` always adds `"defuse:decline"` at lines 142–150; `Game._apply_defuse` eliminates the player on that action at lines 497–513.
- Expected: Under the approved adjudication, a held Defuse must be used; voluntary elimination is not a legal choice.
- Implemented: Declining is legal regardless of whether the player holds a Defuse.

4. Retrieving a Kitten with a five-card combination wrongly triggers an explosion

- Canonical facts: `FIVE-01`, `FIVE-02`
- Evidence type: `human_decision`
- Rule quotes, page 2, “Fünfling” and “Exploding Kitten”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” / “Wenn du ein Exploding Kitten ziehst …”
- Conflicting code: `Game._resolve_pending`, `kind == "five"`, lines 453–465.
- Expected: A retrieved Kitten enters the player’s hand without exploding because it was taken from the discard rather than drawn from the draw pile.
- Implemented: The retrieved Kitten is not put into the hand; instead the game enters the `defuse` phase, where the player must Defuse it or be eliminated.

5. Empty-handed players are exposed as legal Favor and pair targets

- Canonical facts: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rule quotes, page 2: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.” / “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Conflicting code: `Game.legal_actions` uses `_other_alive` without checking target hands at lines 159–167. Resolution silently does nothing for an empty target at lines 430–443.
- Expected: Empty-handed players are not legal targets for Favor or pair theft.
- Implemented: They remain legal targets, producing a discarded action with no transfer.

6. A held Exploding Kitten cannot be requested through a triple

- Canonical facts: `TRI-01`, `TRI-02`, `FIVE-02`
- Evidence type: `human_decision`
- Rule quotes, page 2: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.” / “Besitzt er solch eine Karte, muss er sie dir geben.”
- Conflicting code: `REQUESTABLE_CARDS`, lines 28–36, omits `EXPLODING`; triple actions are generated exclusively from that tuple at lines 169–174.
- Expected: Once the approved five-card ruling allows a Kitten to exist in a hand, its title may be requested like another held card.
- Implemented: No triple action can request an Exploding Kitten.

No critical or minor findings.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Setup and card counts | Represented consistently with `SET-01`–`SET-07` |
| Hidden hands/deck | Basic representation present; observation secrecy is only partial |
| Normal turn and draw | Correct basic play-or-pass-then-draw structure |
| Attack | Major debt and transfer errors |
| Skip | Major error under Attack |
| Defuse/elimination | Reinsertion and discard mostly correct; illegal decline choice |
| Future/Shuffle | Expected top-card preview and deck-only shuffle represented |
| Favor/pair/triple | Core effects present; target/request legality errors |
| Nope reactions | Toggle and discard behavior represented; exact priority remains adjudication-dependent |
| Five-card combination | Self-retrieval supported, but Kitten retrieval is wrong |
| Terminal result/returns | Sole-survivor terminal condition and `+1/-1` returns represented |

## Missing deterministic scenarios

- Normal Attack gives the next player exactly two turns.
- Counter-Attack transfers exactly two turns to the following player.
- One Skip during Attack leaves one owed turn; two Skips consume both.
- A player holding Defuse has no decline action.
- Defusing the first of two owed turns preserves the second obligation.
- Five-card retrieval puts an Exploding Kitten safely into hand.
- A retrieved Kitten can participate in a combination and be requested by triple.
- Empty-handed players are excluded from Favor and pair target actions.
- Elimination during Attack removes the eliminated player’s remaining debt.
- A five-card combination can retrieve one of its own newly discarded components.

## Material questions for a human

- `FIVE-02` permits the only two-player Kitten to be removed from the draw pile and retained in a hand. What should happen if this makes elimination impossible and the draw pile later becomes empty? The implementation raises `RuntimeError`, while the printed assurance that the pile never empties assumes Kittens remain capable of being drawn.
- Should player-specific observations be added to enforce the secrecy of hands, Future previews, and Defuse reinsertion choices? The current state object exposes all hands directly, while `render` only partially models private viewing.

score: 0.42
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true