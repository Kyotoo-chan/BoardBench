## Review result

`score: 0.79` — `confidence: high`

The implementation covers setup, normal turn flow, named-card effects, combinations, elimination, terminal returns, and Attack obligations well. The principal defects are three explicitly illegal choices: voluntary explosion despite holding Defuse, Favor targeting an empty hand, and Pair targeting an empty hand.

## Findings

### Major 1 — A player may voluntarily explode despite holding a Defuse

- Canonical fact ID: `DEF-01`
- Evidence type: `human_decision`
- Rule quote: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.” — page 2, “Entschärfung”
- Approved adjudication: If the player possesses a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting code: `Game.legal_actions`, branch `state.phase == "defuse"`, always initializes `actions = ["explode"]` and merely adds `"defuse:use-protection"` when Defuse is held. `Game.apply_action` then accepts `"explode"` and calls `_eliminate`.
- Expected: With a Defuse in hand, the only legal resolution is to use it and proceed to secret reinsertion.
- Implemented: The player can choose immediate elimination, potentially producing a winner that cannot arise under the approved rules.

### Major 2 — Favor may target an empty-handed player

- Canonical fact ID: `FAV-01`
- Evidence type: `human_decision`
- Rule quote: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.” — page 2, “Wunsch”
- Approved adjudication: Empty-handed players are not legal targets.
- Conflicting code: `Game.legal_actions` constructs Favor actions from every living opponent in `other_players`, without checking `state.hands[target]`. `_resolve_pending`, branch `kind == "favor"`, silently turns an empty target into a no-effect action.
- Expected: No Favor action naming an empty-handed target should be legal.
- Implemented: The actor may discard Favor, pass through the Nope window, and receive nothing from an invalid target.

### Major 3 — A Pair may target an empty-handed player

- Canonical fact ID: `PAIR-01`
- Evidence type: `human_decision`
- Rule quote: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.” — page 2, “Pärchen”
- Approved adjudication: Empty-handed players are not legal targets.
- Conflicting code: `Game.legal_actions` generates Pair actions for every living opponent regardless of hand size. `_resolve_pending`, branch `kind == "pair"`, silently resolves an empty target without a theft.
- Expected: Empty-handed opponents must be excluded from Pair target actions.
- Implemented: Two cards can be discarded for a Pair against an invalid target with no resulting transfer.

No critical or minor contradictions were identified.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Correct seven-card deal, starting Defuse, Kittens, and two-player Defuse variant |
| Hidden setup information | Covered | Deck shuffled; rendered hands are limited to the acting player |
| Normal turn flow | Covered | Zero or more plays followed by draw |
| Attack and Skip | Covered | Two owed turns, replacement Attack, and one-turn Skip behavior represented |
| Explosion and Defuse | Defective | Voluntary explosion remains legal while Defuse is held |
| Elimination and terminal result | Covered | Hand and Kitten discarded; sole survivor and `+1/-1` returns correct |
| Preview and Shuffle | Covered | Top three/all remaining previewed without reordering; shuffle affects deck |
| Favor | Defective | Empty-handed targets incorrectly legal |
| Pair | Defective | Empty-handed targets incorrectly legal |
| Triple | Mostly covered | Named request and conditional transfer implemented |
| Five-card combination | Covered | Five distinct titles discarded first; own component or Kitten can be recovered |
| Nope chain | Covered | Toggle chain, discarded cards, and continued actor turn represented |
| Private choices | Mostly covered | Reinsertion and preview are recorded privately, though state-level visibility needs an API decision |

## Missing deterministic scenarios

- A player draws a Kitten while holding Defuse: assert `"explode"` is absent and Defuse use is mandatory.
- Favor with one empty-handed and one nonempty opponent: only the nonempty opponent is targetable.
- Pair under the same target arrangement: only the nonempty opponent is targetable.
- Defuse during the first of two Attack turns: reinsertion ends only that individual turn, leaving the second owed turn.
- Attack played during an owed Attack turn: the following player owes exactly two turns, not accumulated turns.
- Elimination during an Attack obligation: remaining owed turns disappear.
- Five-card retrieval of one just-discarded component.
- Five-card retrieval of an Exploding Kitten, followed by confirmation that it remains harmless in hand.
- Multi-player Nope–Nope chain, confirming cancellation toggling and continued original turn.
- Two-player versus three-player setup, checking the different additional-Defuse counts.

## Material questions for a human

- `REQUESTABLE` excludes Exploding Kitten as a Triple’s requested title. The packet confirms that a recovered Kitten may be held and participate in same-title combinations, but does not expressly decide whether it may be the requested title in a Triple. This should remain a question rather than a scored defect.
- Is direct access to `GameState.pending`, `hands`, `deck`, and `observations` considered part of an omniscient engine API, or must all consumers be restricted to `render()`? The answer affects whether pending targets and secret information are adequately exposed or protected.

score: 0.79
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true