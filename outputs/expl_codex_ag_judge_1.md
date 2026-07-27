## 1. Score

**Score: 0.90 — confidence: high.**

The implementation is broadly faithful across setup, normal turns, card effects, information hiding, elimination, terminal state, and returns. One clear material contradiction affects chained Attacks. Remaining concerns depend on unresolved source questions and are therefore not scored as rule violations.

## 2. Findings

### Major — Chained Attack assigns three turns instead of exactly two

- Canonical fact: `EXPL-C-ATTACK-CHAIN`
- Evidence type: `rule_quote`
- Source: `EXPL-NSFW-DE-2018-RULES`
- Locator: `canonical_rulebook.pdf`, page 2
- Exact evidence: “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Conflicting transition: [`Game._resolve_proposed()` attack branch](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-qMUh81/boardbench_expl_codex_ag_judge_1_wxiopyvj/implementation.py:194), specifically `s.turns_owed = s.turns_owed + 1`.
- Expected: If an attacked player plays Attack during either owed turn, their remaining obligation ends and the following living player owes exactly two turns.
- Implemented: When Attack is played during the first of two owed turns, `turns_owed` is 2 and the code transfers `2 + 1 = 3` turns to the next player.
- Required change: Set the recipient’s debt to exactly `2`, rather than incrementing the current player’s debt.

### Questions — not scored as contradictions

1. **Empty-handed Triple target**

   `legal_actions()` uses `_opponents_with_cards()` for Triple as well as Favor and Pair. The supplement’s `EXPL-D-EMPTY-TARGET` decision expressly names only Favor and Pair. Meanwhile, `EXPL-C-TRIPLE-LACKS` says that when the target lacks the requested card, nothing transfers. The packet does not conclusively state whether an entirely empty opponent remains a legal Triple target.

2. **Stale See-the-Future preview**

   A player’s `preview` is cleared only when that player draws. It remains unchanged after Shuffle, Attack/Skip followed by another player’s draw, or other draw-pile mutations. `EXPL-C-FUTURE-THREE`, `EXPL-C-FUTURE-ORDER`, and `EXPL-C-SHUFFLE` establish what was seen and that Shuffle changes pile order, but do not specify whether the digital `preview` field represents current top cards or persistent memory.

3. **Five-card self-retrieval timing**

   Five-card actions are enumerated before their five components enter discard, so the implementation cannot retrieve one of those just-played components and cannot play the combination against an initially empty discard. `EXPL-A-FIVE-SELF-RETRIEVE` explicitly leaves this unresolved. This is not penalized.

4. **Automatic Defuse**

   Drawing a Kitten while holding Defuse automatically consumes it. `EXPL-A-DEFUSE-OPTIONAL` leaves voluntary elimination unresolved, so this is an implementation assumption rather than a scored contradiction.

5. **Nope protocol and restored empty targets**

   The implementation chooses a deterministic responder order and exposes parameterized actions before reactions. Priority, announcement timing, and restoration after a target spends its final card are explicitly unresolved by `EXPL-M-NOPE-PRIORITY`, `EXPL-M-NOPE-ANNOUNCEMENT`, and `EXPL-M-NOPE-EMPTY-RESTORE`.

## 3. Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Inventory and player counts | Pass | Correct 56-card composition and 2–5-player validation |
| Setup and dealing | Pass | Seven ordinary cards plus one Defuse; correct Kittens, extra Defuses, and boxed cards |
| Turn flow | Pass | Zero or more plays followed by draw; clockwise living-player advancement |
| Attack/Skip debt | **Fail** | Ordinary Attack and Skip work; first-turn chained Attack creates three-turn debt |
| Kitten, Defuse, elimination | Pass | Reinsertion range/order, discard, debt expiration, and terminal handling are represented |
| Nope reactions | Pass with unresolved assumptions | Cancellation, parity, off-turn use, and discard retention implemented |
| Favor, Pair, Triple | Pass/question | Favor and Pair honor empty-target clarification; Triple empty-target legality undecided |
| Shuffle/Future | Pass/question | Correct pile conservation and private top-to-bottom preview; persistence semantics unclear |
| Five-card combination | Pass/question | Distinct titles and effect suppression work; self-retrieval timing unresolved |
| Private/public information | Pass | Hands and preview are observation-private; pile size and discard are public |
| Terminal and returns | Pass | Immediate sole-survivor win; winner `+1`, others `-1` |

## 4. Missing deterministic scenarios

Recommended focused scenarios:

- An attacked player plays Attack during the **first** owed turn; assert that the following player owes exactly two turns.
- The same chain during the **second** owed turn, to prevent overcorrecting the first case.
- Two-player and multi-player Attack chains with eliminated seats between actor and recipient.
- Favor and Pair action enumeration against empty versus nonempty opponents, covering `EXPL-D-EMPTY-TARGET`.
- See the Future followed by Shuffle, Skip/Attack, and another player’s draw, once preview persistence semantics are decided.
- Explosion while holding several cards, asserting that the complete hand and Kitten enter discard before terminal evaluation.
- A restored targeted action whose target spent its final card as Nope, once the packet defines the result.

## 5. Material human decisions needed

- Is an empty-handed living opponent a legal Triple target?
- What must `preview` contain after the draw pile changes?
- May a five-card combination retrieve one of its own newly discarded components, including when discard was previously empty?
- May a player voluntarily decline Defuse?
- What deterministic Nope priority/window protocol should the module expose?
- How should a restored Favor or combination resolve if its target became empty during the Nope chain?

score: 0.90
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true