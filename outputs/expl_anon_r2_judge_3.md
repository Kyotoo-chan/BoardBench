## Assessment

Score: **0.91**  
Confidence: **high**

The implementation closely matches setup, turn sequencing, Attack obligations, Defuse reinsertion, elimination, Nope chains, combinations, terminal conditions, and returns. The material defect is that empty-handed players remain legal targets for Favor and Pair, causing cards to be discarded for an action the approved facts declare illegal.

## Findings

### Major — Empty-handed targets are legal for Favor and Pair

- Canonical facts: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rulebook quotes, page 2:
  - Favor/Wunsch: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
  - Pair/Pärchen: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Complete approved expectations:
  - Favor transfers a card selected by the target; empty-handed players are not legal targets.
  - Pair steals a random card; empty-handed players are not legal targets.
- Conflicting symbols/transitions:
  - `Game.legal_actions`, lines 122–128, generates both action types for every other living player without checking their hand.
  - `Game._resolve_pending`, lines 235–243, conditionally does nothing when the target is empty.
- Expected: no Favor or Pair action targeting an empty-handed player appears in `legal_actions`.
- Implemented: the action is legal; its component card or pair is discarded, the Nope window runs, and the effect silently does nothing.
- Impact: materially incorrect action legality and resource expenditure in two stealing mechanics.

### Question — May a powerless Cat card be played singly?

- Canonical context: `COMBO-01`
- Page 2, Cat cards: “Einzeln sind diese Karten machtlos, doch wenn du 2 gleiche Katzen-Karten hast, kannst du sie als Pärchen spielen …”
- `PLAYABLE` and `_resolve_pending` allow each symbol/Cat card to be played singly and discarded with no effect.
- The packet establishes that a single Cat card has no power, but does not unambiguously decide whether it may nevertheless be played and discarded. This should not be scored without a human decision.

### Question — Raw-state privacy boundary

- Canonical fact: `SET-08`
- Rule quote, page 1/setup: “Halte dein Blatt stets verdeckt.”
- `render` hides other players’ hands and shows private preview information only to the current decision-maker. However, `GameState.hands` and `knowledge` remain directly accessible.
- The approved facts explicitly say secrecy cannot be fully verified without player-specific observations. Whether raw state is privileged engine data or player-visible API data therefore needs an interface decision.

No critical or minor contradictions were identified.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup | Conforms | Correct deal, starting Defuse, Kittens, and two-player Defuse variant |
| Turn flow | Conforms | Zero-or-more plays, mandatory draw, clockwise living-player order |
| Attack and Skip | Conforms | Owed turns, replacement Attack, Skip consumption, elimination reset |
| Explosion and Defuse | Conforms | Forced Defuse, explicit reinsertion, discard and elimination behavior |
| Nope reactions | Conforms | Out-of-turn windows, toggling, discarded cancelled cards |
| Favor and Pair | Defect | Empty-handed targets incorrectly remain legal |
| Triple | Conforms | Explicit target/request; transfer only when held |
| Five-card combination | Conforms | Five distinct titles; retrieval includes newly discarded components and Kittens |
| Preview and Shuffle | Conforms | Private top-three preview; shuffle changes deck order |
| Private information | Partial/question | Renderer is perspective-sensitive; raw-state boundary unspecified |
| Terminal and returns | Conforms | Immediate sole-survivor terminal state; `+1/-1` returns |

## Recommended deterministic scenarios

- Empty-handed players are absent from Favor target actions.
- Empty-handed players are absent from Pair target actions.
- A Defuse during the first of two owed Attack turns leaves one turn owed.
- An Attack during an owed turn replaces the remaining obligation with exactly two turns for the following player.
- A cancelled Attack or Skip leaves the actor in the same individual turn.
- Nope–Nope toggling resolves the underlying action and keeps all played cards discarded.
- Five distinct cards can retrieve one of their own just-discarded components.
- A discarded Kitten retrieved by a five-card combination enters the hand without exploding.
- Preview with fewer than three deck cards reveals all remaining cards privately.
- An empty-handed player retains `draw` as a legal action.

## Material questions for a human

1. Does “Einzeln sind diese Karten machtlos” permit playing and discarding one Cat card for no effect, or are Cat cards playable only in combinations?
2. Is direct inspection of `GameState` privileged engine access, or must player-specific observations prevent access to opponents’ hands and previews?

```text
score: 0.91
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```