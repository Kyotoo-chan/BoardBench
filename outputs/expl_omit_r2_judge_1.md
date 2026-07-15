score: 0.64  
confidence: high

Rationale: setup, normal turn flow, Attack/Skip accounting, Nope chains, elimination, terminal returns, and most named cards are implemented faithfully. However, one complete combination is absent, Defuse is incorrectly optional, and empty-handed targets remain legal for actions where approved facts prohibit them.

## Findings

### Major

1. Defuse can be declined, allowing voluntary elimination

- Canonical fact ID: `DEF-01`
- Evidence type: `human_decision`
- Rule quote: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.” Page 2, “Entschärfung”.
- Approved complete fact: If the player has a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting transition: `Game.legal_actions()`, phase `"exploding"`, always includes `Action("explode")`, even when `DEFUSE in hand`.
- Expected: A player holding Defuse has only the Defuse response, followed by explicit reinsertion.
- Implemented: The player may select `exploding:explode`, discard their hand, and be eliminated despite holding Defuse.
- Impact: This illegal choice can change the winner, including immediately in a two-player game.

2. The five-distinct-title combination is entirely absent

- Canonical fact ID: `FIVE-01`
- Evidence type: `rule_quote`
- Rule quote: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” Page 2, “Kombinationen – Fünfling”.
- Approved complete fact: The five cards enter the discard first, and the player may retrieve any chosen card now present there, including an Exploding Kitten or one of those five components.
- Conflicting symbols: `Game.legal_actions()` and `Game.apply_action()` have no five-card action, retrieval phase, or discard-card choice. `Game.ASSUMPTIONS` explicitly says the combination is omitted.
- Expected: Five distinct titles form a Nope-able combination with an explicit retrieval choice after discarding its components.
- Implemented: No such legal action or transition exists.
- Impact: A material, explicitly printed combination and its discard-retrieval strategy are unavailable.

3. Empty-handed players are legal Favor and Pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rule quotes:
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.” Page 2, “Wunsch”.
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.” Page 2, “Kombinationen – Pärchen”.
- Approved complete facts: Empty-handed players are not legal targets for Favor or Pair.
- Conflicting symbols: `Game.legal_actions()` constructs `opponents` from living status only and generates `favor` and `pair` actions for every such opponent. `_close_reaction()` silently produces no transfer when the selected hand is empty.
- Expected: Empty-handed opponents must be omitted from the target choices.
- Implemented: These targets are legal; the card or pair is discarded, passes through the reaction window, and then has no effect.
- Impact: Players can spend cards on actions that the approved rules say are not legal.

### Minor

4. Exploding Kitten cannot be requested by a Triple

- Canonical fact IDs: `TRI-01`, `TRI-02`, `FIVE-02`
- Evidence type: `human_decision`
- Conflicting symbol: `REQUESTABLE` excludes `EXPLODING`.
- Expected: Once a Kitten has legally entered a hand through five-card retrieval, it remains a card title and can participate in same-title combinations, including being requested by a Triple.
- Implemented: No Triple action can name an Exploding Kitten.
- Impact: Currently unreachable because five-card retrieval is itself omitted, but it would remain wrong after that omission is repaired.

## Coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Seven dealt cards plus Defuse; correct Kitten and extra-Defuse counts |
| Hidden setup information | Mostly covered | Deck shuffled; hands represented separately |
| Normal turn flow | Covered | Zero or more plays followed by draw |
| Attack and Skip | Covered | Owed-turn replacement and one-turn consumption agree with adjudications |
| Explosion and Defuse | Incorrect | Reinsertion is explicit, but illegal voluntary explosion is offered |
| Elimination and terminal result | Covered | Hand and Kitten discarded; sole survivor wins; returns are ±1 |
| See the Future | Covered | Up to three cards, order unchanged |
| Shuffle | Covered | Only deck order changes |
| Favor | Incorrect edge case | Explicit donation choice works; empty targets remain legal |
| Nope | Covered | Reactions, parity toggling, cancellation, and discarded cards represented |
| Pair | Incorrect edge case | Random theft works; empty targets remain legal |
| Triple | Mostly covered | Explicit requested title, but Kitten excluded |
| Five-card combination | Missing | No play, reaction, or retrieval transition |
| Public/private information | Partially covered | Rendering limits hand display; raw state remains omniscient, an acknowledged test limitation |

## Missing deterministic scenarios

- A player with Defuse draws a Kitten and has no legal voluntary-elimination action.
- Defuse under Attack consumes one owed turn and preserves any further owed turn.
- Five distinct titles are discarded before retrieval.
- Five-card retrieval can select one of its own five components.
- Five-card retrieval can put a discarded Exploding Kitten into hand without triggering it.
- A five-card combination can be Noped, leaving all five components discarded.
- Empty-handed opponents are absent from Favor targets.
- Empty-handed opponents are absent from Pair targets.
- A Triple can request an Exploding Kitten once one is present in the target’s hand.
- Multiple Nope toggles preserve the underlying action on even parity.

## Material questions for a human

None required for the scored findings. Exact physical Nope timing and full enforcement of player-specific observations remain acknowledged, non-hard-testable limitations rather than code findings.

score: 0.64
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true