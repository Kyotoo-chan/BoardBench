Score: 0.74, confidence: high. The implementation covers setup, turn sequencing, named cards, combinations, elimination, and returns well. Three material legal-action deviations remain. This was a static review only; the code was not executed.

## Findings

### Major — Defuse can be declined

This is an adjudication-dependent deviation, not a contradiction of the printed word “kann.”

- Canonical fact: `DEF-01`
- Evidence type: `human_decision`
- Rule quote: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.” Page 2, “Entschärfung”
- Approved decision: A held Defuse must be used; voluntary elimination is not offered.
- Conflicting code: `_legal_actions`, phase `"exploding"`, always includes `"accept:explode"`; `_apply_action` sends that action to `_eliminate`.
- Expected: When the player holds a Defuse, only `use:defuse` is legal.
- Implemented: The player can choose `accept:explode`, potentially eliminating themselves and immediately awarding another player the game.

### Major — Favor may target an empty-handed player

This is an adjudication-dependent target-legality deviation.

- Canonical fact: `FAV-01`
- Evidence type: `human_decision`
- Rule quote: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.” Page 2, “Wunsch”
- Approved decision: Empty-handed players are not legal targets.
- Conflicting code: `_legal_actions` constructs Favor actions from every living opponent returned by `_opponents`, without checking their hand. `_resolve_pending`, branch `kind == "favor"`, silently resolves an empty target with no transfer.
- Expected: No Favor action targeting an empty-handed player appears in `legal_actions`.
- Implemented: The action is legal, consumes and discards Favor, then has no effect.

### Major — Pair theft may target an empty-handed player

This contradicts the approved target requirement implicit in performing a random-card theft.

- Canonical fact: `PAIR-01`
- Evidence type: `rule_quote`
- Rule quote: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.” Page 2, “Pärchen”
- Approved expectation: Empty-handed players are not legal targets.
- Conflicting code: `_legal_actions` creates pair actions for every living opponent. `_resolve_pending`, branch `kind == "pair"`, silently does nothing when the selected hand is empty.
- Expected: Only opponents holding at least one card are legal pair targets.
- Implemented: Two cards can be discarded against an empty target without stealing a card.

No critical or minor findings identified.

## Rule-area coverage

| Area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Correct seven-card deal, starting Defuse, Kittens, and two-player Defuse variant |
| Hidden information | Mostly covered | Rendering hides other hands and Future preview; raw state remains directly inspectable |
| Normal turn flow | Covered | Zero or more plays followed by draw; Skip and Attack end individual turns |
| Attack obligations | Covered | Two owed turns, replacement Attack, Skip consumption, Defuse continuation, and elimination reset align with approved decisions |
| Explosion/Defuse | Deviation | Defuse can incorrectly be declined |
| Elimination/terminal/returns | Covered | Hand and Kitten discarded; sole survivor receives `+1`, others `-1` |
| Future/Shuffle | Covered | Top three or fewer, preserved order, private preview, deck-only shuffle |
| Favor | Deviation | Empty-handed targets incorrectly legal |
| Nope | Covered | Out-of-turn cycle, parity toggling, discarded cancelled cards, and continued actor turn |
| Pair | Deviation | Empty-handed targets incorrectly legal |
| Triple | Covered | Named request and conditional transfer |
| Five-card combination | Covered | Components enter discard before retrieval and may themselves be retrieved |
| Discarded Kitten retrieval | Covered | It enters the hand without exploding and is restricted to combinations |
| Action conversion/interface | Covered | Stable string actions and explicit rule choices |

## Missing deterministic scenarios

- A player holding Defuse must not receive `accept:explode`.
- A Favor action must exclude every empty-handed opponent.
- A pair action must exclude every empty-handed opponent.
- In a two-player game, declining a held Defuse must not provide an illegal terminal path.
- Defusing the first of two Attack turns must leave exactly one turn owed.
- An Attack played during an Attack must replace the remaining obligation with exactly two turns for the following player.
- Odd and even Nope chains should respectively cancel and restore an action.
- Five-card retrieval should permit one of the five newly discarded components.
- Retrieving a discarded Kitten should place it safely in hand and permit combination use.
- Elimination should discard the complete hand plus the drawn Kitten before terminal returns are exposed.

## Material questions for a human

- Does “Einzeln sind diese Karten machtlos” permit a Cat card to be played and discarded singly as a no-op? The implementation allows this, but the packet does not explicitly settle legality.
- Must announced reaction parameters such as Favor targets and Triple requested titles appear in `render()`, or is their presence in public `pending` state sufficient?
- Is direct programmatic access to every entry in `state.hands` acceptable for this API, given that the approved facts acknowledge that private information cannot be fully verified?
- May the original actor participate in the Nope cycle against their own action? The packet leaves physical reaction timing and priority ambiguous.

score: 0.74
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true