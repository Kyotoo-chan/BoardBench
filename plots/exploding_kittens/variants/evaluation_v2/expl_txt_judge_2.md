## Assessment

`score: 0.78`  
`confidence: high`

The implementation models setup, ordinary turn flow, Attack/Skip obligations, Nope chains, combinations, elimination, terminal returns, and five-card self-retrieval well. The main defects are three explicit legal-action contradictions involving mandatory Defuse use and empty-handed targets.

## Findings

### Major — Voluntary elimination is offered despite holding a Defuse

- Canonical fact: `DEF-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Approved decision: If the player has a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting code: `_legal_actions()` at `implementation.py:252-254`; `_apply_action()` at `implementation.py:504-505`.
- Expected: A player holding Defuse has only `use:defuse`.
- Implemented: `accept:explode` remains legal alongside `use:defuse`, allowing intentional elimination and potentially changing the winner.

### Major — Favor can target an empty-handed player

- Canonical fact: `FAV-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “Wunsch”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
- Complete approved expectation: The target selects and transfers a card; empty-handed players are not legal targets.
- Conflicting code: `_opponents()` at `implementation.py:218-223`; Favor action construction at `implementation.py:279-281`; `_resolve_pending()` at `implementation.py:378-385`.
- Expected: Only living opponents with at least one card appear as Favor targets.
- Implemented: Every living opponent is offered. An empty target makes the discarded Favor resolve without a transfer.

### Major — Pair theft can target an empty-handed player

- Canonical fact: `PAIR-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “Pärchen”: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Complete approved expectation: Any two same-title cards steal one random card; empty-handed players are not legal targets.
- Conflicting code: `_opponents()` at `implementation.py:218-223`; pair action construction at `implementation.py:283-288`; `_resolve_pending()` at `implementation.py:388-395`.
- Expected: Only nonempty-handed living opponents are legal pair targets.
- Implemented: An empty opponent can be selected, consuming both cards while stealing nothing.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup | Pass | Correct ordinary-card deal, starting Defuses, Kittens, and two-player Defuse variant |
| Turn flow | Pass | Zero or more plays followed by draw; Skip and Attack end individual turns correctly |
| Explosion/Defuse | Major issue | Resolution and reinsertion work, but voluntary death is incorrectly legal |
| Elimination/terminal | Pass | Hand and Kitten discarded; sole survivor and `+1/-1` returns correct |
| Attack obligations | Pass | Two owed turns, replacement Attack, Defuse/Skip consumption, and elimination handling align |
| Future/Shuffle | Pass | Private top-three view and deck-only shuffle represented |
| Favor | Major issue | Donor chooses the card, but empty targets are legal |
| Nope | Pass | Out-of-turn reaction, toggling, cancellation, and discarded cards represented |
| Pair | Major issue | Random theft works for nonempty targets |
| Triple | Pass | Requested-title transfer is explicit and conditional |
| Five-card combination | Pass | Cards enter discard before retrieval; self-retrieval and Kitten retrieval are allowed |
| Information | Pass with limitation | Rendering hides other hands and future views; raw state remains inspectable, but the facts explicitly mark secrecy as not fully verifiable |
| Action naming/returns | Pass | Stable string actions and approved return convention |

## Missing deterministic scenarios

- A player drawing a Kitten while holding Defuse must not receive `accept:explode`.
- Favor with one empty and one nonempty opponent must expose only the nonempty target.
- Pair theft with one empty and one nonempty opponent must expose only the nonempty target.
- Defuse during the first of two Attack-owed turns must leave exactly one turn owed.
- Attack during an owed turn must replace the obligation with exactly two turns for the following player.
- Five distinct cards must permit retrieving one just-discarded component.
- Five-card retrieval of a discarded Kitten must place it harmlessly in hand.
- Odd and even Nope chains should respectively cancel and restore an announced parameterized action.
- Elimination should discard the entire hand plus Kitten and become terminal immediately when only one player remains.

## Material questions for a human

- Page 2 says Cat cards are individually “machtlos.” Does that mean they may be played singly for no effect, as implemented, or that single-card play is illegal? The approved facts do not decide this.
- If single powerless Cat-card play is legal, should it open a Nope reaction window despite having no operative instruction?

score: 0.78
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true