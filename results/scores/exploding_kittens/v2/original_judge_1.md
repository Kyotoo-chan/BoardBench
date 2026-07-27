## 1. Score

`score: 0.80` — `confidence: high`

The implementation covers most of the declared 2–5-player base game correctly, including setup arithmetic, turn progression, Attack debt, Defuse reinsertion, Nope parity, private observations, combinations, terminal detection, and returns. Two material defects remain: exploded hands are not discarded, and the approved empty-target restriction is absent, permitting a reachable Favor deadlock.

## 2. Findings

### Major — Explosion does not discard the player’s remaining hand

- Canonical fact: `EXPL-C-ELIMINATE-DISCARD`
- Evidence type: `rule_quote`
- Source: `EXPL-NSFW-DE-2018-RULES`
- Locator: PDF page 2
- Exact evidence: “Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.”
- Conflicting transition: `Game._draw`, lines 220–233
- Implemented behavior: the Kitten enters `zones["discard"]` and the player becomes dead, but their hand remains unchanged.
- Expected behavior: the Kitten and every card remaining in the exploded player’s hand must enter discard, leaving that hand empty.

This changes the public discard, card conservation, discard retrieval possibilities, and observed hand sizes. Terminal detection itself remains correct.

### Major — Empty-handed Favor and Pair targets remain legal

This is adjudication-dependent, not a contradiction of an unambiguous printed target rule.

- Canonical fact: `EXPL-X-EMPTY-TARGET`
- Evidence type: `human_decision`
- Source: `EXPL-V2-CLAIMS`
- Locator: JSON Pointer `/claims/71/expectation`
- Exact evidence: “Evaluator decision: empty-handed players are illegal Favor and Pair targets.”
- Conflicting symbols:
  - `Game.legal_actions`, lines 134–147
  - `Game._resolve`, lines 249–263
- Implemented behavior:
  - `opponents` includes every living opponent without checking hand size.
  - Favor and Pair actions targeting an empty-handed player are offered.
  - Pair silently resolves without stealing.
  - A successful Favor enters `favor_give`; because the empty target has no `give_card` action, the game reaches a nonterminal state with no legal actions.
- Expected behavior: empty-handed opponents must be excluded from Favor and Pair targets.

### Question — Defuse is mandatory when held

- Canonical fact: `EXPL-A-DEFUSE-OPTIONAL`
- `Game._draw`, lines 213–219, automatically consumes a Defuse whenever one is present.
- The packet leaves voluntary elimination while holding Defuse unresolved. This assumption must not reduce the score.

### Question — Nope response protocol is implementation-defined

- Canonical facts: `EXPL-M-NOPE-PRIORITY`, `EXPL-M-NOPE-ANNOUNCEMENT`
- `Game._start_reaction` and `_advance_reaction`, lines 157–192, impose clockwise response circuits and close the window after a complete pass.
- Targets and triple requests are placed into the pending action before reactions begin.
- The supplied rulebook does not determine either policy. No penalty applied.

### Question — Restored Favor may deadlock after its target spends the last card

- Canonical fact: `EXPL-M-NOPE-EMPTY-RESTORE`
- If a nonempty Favor target plays its last card as a Nope and the Favor is subsequently restored, lines 249–252 enter `favor_give` with an empty target.
- The packet explicitly leaves this reaction-chain case unresolved. A human resolution policy is required before treating it as a code defect.

### Question — Five-card self-retrieval policy is conditional

- Canonical fact: `EXPL-A-FIVE-SELF-RETRIEVE`
- `legal_actions`, lines 149–154, only offers titles already present in discard before the five cards are played. Consequently, a newly discarded component cannot be selected unless another copy of that title was already present.
- `_resolve`, lines 270–273, then retrieves the newest matching card, which can be the just-played component.
- The packet expressly leaves immediate component retrieval unresolved. The permitted self-retrieval behavior is not penalized.

No minor findings.

## 3. Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Inventory and 2–5-player setup | Covered | Counts, seven-card deal, starting Defuse, Kittens, and two-player boxing align |
| Normal turn flow | Covered | Zero or more plays followed by top-card draw |
| Clockwise/debt progression | Covered | Living-player advancement and individual Attack turns represented |
| Explosion/elimination | Defective | Elimination works, but remaining hand is not discarded |
| Defuse/reinsertion | Covered | Top/bottom positions, hidden deck, order preservation, and debt continuation align |
| Attack and Skip | Covered | Attack assigns two turns; chaining replaces debt; Skip consumes one turn |
| Nope | Covered with questions | Cancellation, parity, off-turn play, and discard retention align |
| Favor and Pair targets | Defective | Empty targets are legal; Favor can deadlock |
| Shuffle/See the Future | Covered | Deck conservation and private top-to-bottom preview align |
| Pair/Triple/Five combinations | Covered with question | Same-title/distinct-title rules and effect suppression align |
| Private/public information | Covered | Hands and previews are private; discard and pile size are public |
| Terminal/winner/returns | Covered | Sole survivor immediately wins; returns are consistent |

## 4. Missing deterministic scenarios

Highest-value deterministic scenarios to add:

1. Explode while holding several cards; assert the Kitten and complete hand enter discard and the hand becomes empty.
2. With an initially empty opponent, assert no Favor or Pair action targeting that player is legal.
3. Attempt the currently permitted empty-target Favor sequence; assert it cannot produce a nonterminal zero-action state.
4. Once adjudicated, test a Favor target spending its final card during a Nope chain.
5. Once adjudicated, test five-card retrieval both with and without a preexisting discard copy of a component title.
6. Once adjudicated, test whether a player holding Defuse may decline to use it.

## 5. Material questions for a human

- May a player voluntarily explode while holding a Defuse?
- What deterministic Nope response order and window-closing protocol should the module expose?
- Must targets and requested titles be committed before the Nope window?
- What happens when a restored Favor targets a player who spent their final card in the reaction chain?
- May a five-card combination retrieve one of the five components it just discarded?

```text
score: 0.80
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```