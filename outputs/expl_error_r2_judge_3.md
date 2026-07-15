score: 0.52  
confidence: high

Setup, normal drawing, Attack replacement, Nope chains, elimination, terminal results, and most named-card effects are substantially represented. The score is reduced by five clear, material contradictions affecting legal actions and state transitions.

## Findings

### Major

1. Skip incorrectly cancels the entire remaining Attack obligation

- Canonical fact ID: `SKIP-02`
- Evidence type: `rule_quote`
- Rule quote, page 2, “Hops!”: “Falls du „Hops!“ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal „Hops!“ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `Game._settle_pending`, `kind == "skip"`
- Expected: When `turns_left == 2`, one Skip consumes one owed turn; the attacked player remains current with one turn still owed.
- Implemented: `_advance_to(..., self._next_alive(...), 1)` immediately advances to the next player, cancelling both owed turns.

2. A player holding Defuse may choose voluntary elimination

- Canonical fact ID: `DEF-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Approved decision: If the player has a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting code: `Game.legal_actions`, `state.phase == "defuse"`; `Game.apply_action`
- Expected: With Defuse in hand, the legal action is to use it.
- Implemented: `explode:voluntarily` remains legal alongside `react:Entschärfung`, allowing avoidable elimination and potentially changing the winner.

3. A five-card combination cannot generally retrieve one of its own components

- Canonical fact ID: `FIVE-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Approved decision: The five components enter the discard before retrieval and may themselves be selected.
- Conflicting code: `Game.legal_actions`, five-card action generation
- Expected: Retrieval choices include the five cards about to be discarded, even if the discard pile was previously empty.
- Implemented: Choices come exclusively from the pre-action `state.discard`; no five-card action exists when that discard is empty. A just-played component is selectable only accidentally when the same title was already present.

4. Retrieving an Exploding Kitten from the discard incorrectly triggers an explosion

- Canonical fact ID: `FIVE-02`
- Evidence type: `human_decision`
- Rule quote, pages 1–2: “Wenn du ein Exploding Kitten ziehst …” / “eine beliebige Karte aus dem Ablagestapel nehmen”
- Approved decision: Taking a Kitten from the discard is not drawing it from the draw pile; it enters the hand without exploding.
- Conflicting code: `Game._settle_pending`, `kind == "five"` and `wanted == EXPLODING`
- Expected: Add the Kitten to the actor’s hand. It cannot be played singly but may be used in a same-title combination.
- Implemented: The game enters `phase = "defuse"`, forcing Defuse or elimination as though the Kitten had been drawn.

5. Empty-handed players remain legal Favor and Pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rule quotes, page 2:
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved decisions: Empty-handed players are not legal targets.
- Conflicting code: `Game.legal_actions`, `others`, Favor and Pair action construction
- Expected: Target lists contain only living opponents with at least one card.
- Implemented: Every living opponent is offered. At settlement, an empty target merely makes the action fizzle after the acting cards have been discarded.

No critical or separately localized minor issue was established from the approved evidence.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and card counts | Pass | Seven dealt cards, one starting Defuse, correct Kitten and extra-Defuse counts |
| Privacy and draw-pile information | Partial | `render` hides other hands, but no player-specific observation boundary exists |
| Normal turn flow | Pass | Zero or more plays followed by draw |
| Explosion and Defuse | Fail | Voluntary elimination is offered despite mandatory-Defuse adjudication |
| Attack | Pass | Assigns exactly two turns; replacement Attack assigns two to the next player |
| Skip under Attack | Fail | One Skip removes the whole obligation |
| Future and Shuffle | Pass | Private top-three state and order-only shuffle are represented |
| Favor | Partial | Donor chooses the card, but empty targets are legal |
| Nope reactions | Pass | Out-of-turn toggling and discarded cancelled actions are represented |
| Pair and Triple | Partial | Effects work; Pair permits empty targets |
| Five-card combination | Fail | Incomplete retrieval choices and wrong Kitten transition |
| Elimination and terminal state | Pass | Hand and Kitten discarded; sole survivor wins |
| Returns | Pass | Nonterminal zeros and terminal `+1/-1` |

## Missing deterministic scenarios

- An attacked player with two owed turns plays one Skip and remains current with one owed turn.
- A player drawing a Kitten while holding Defuse has no voluntary-explosion action.
- Five distinct cards can be played against an initially empty discard and retrieve one component.
- Five-card retrieval of an Exploding Kitten places it harmlessly in hand.
- Favor and Pair exclude empty-handed opponents while still allowing nonempty opponents.
- A Defuse during the first of two attacked turns ends only that individual turn.
- A cancelled Skip or Attack leaves the original actor in the same turn.
- Setup count assertions for every supported player count from two through five.

## Material questions for a human

- If a discarded Kitten is retrieved into a hand and the draw pile later becomes empty while multiple players remain, what transition should replace `draw`? The approved facts permit Kitten retrieval but do not define deck exhaustion.
- Is an omniscient authoritative `GameState` acceptable if only `render` is player-filtered, or must the API provide player-specific observations enforcing `SET-08` and `FUT-02`?
- If a valid nonempty Favor target spends its last card as a Nope during the reaction window and the Favor ultimately resolves, should the Favor fizzle or require some other resolution?

score: 0.52
confidence: high
critical_issues: 0
major_issues: 5
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true