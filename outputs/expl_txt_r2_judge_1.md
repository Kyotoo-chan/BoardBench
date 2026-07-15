score: 0.76  
confidence: high

The implementation covers setup, ordinary turns, Attack obligations, Skip, Defuse reinsertion, elimination, returns, reactions, and most combinations coherently. Two material legal-action errors remain: voluntary explosion despite holding a Defuse, and incomplete five-card retrieval choices.

## Findings

### Major

1. A player may voluntarily explode despite holding a Defuse.

   - Canonical fact: `DEF-01`
   - Evidence type: `human_decision`
   - Rule quote: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.” — page 2, “Entschärfung”
   - Approved decision: If a player has a Defuse, it must be used; voluntary elimination is not offered.
   - Conflicting code: `Game.legal_actions()`, `state.phase == "defuse"`, unconditionally adds `("explode",)`. `Game.apply_action()` then sends that action to `_kill()`.
   - Expected: With a Defuse in hand, only explicit Defuse/reinsertion actions are legal.
   - Implemented: Both Defuse and voluntary elimination are legal. Choosing the latter can change the winner and prematurely terminate the game.

2. Five-card combinations cannot retrieve a newly discarded component unless an equivalent title was already in the discard pile.

   - Canonical fact: `FIVE-01`
   - Evidence type: `human_decision`
   - Rule quote: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” — page 2, “Fünfling”
   - Approved decision: The five cards enter the discard before retrieval, so any one of those components may immediately be retrieved.
   - Conflicting code: `Game.legal_actions()` creates `("five", cards, take)` only for titles already in `state.discard`, and creates no five-card actions at all when the discard is initially empty. `_resolve_effect()` only receives that preselected title.
   - Expected: Retrieval choices are calculated from the discard after the five components have been added, including those components.
   - Implemented: Choices come exclusively from the pre-action discard. A valid five-card combination can therefore be unavailable, and newly discarded component titles can be omitted.

### Minor

3. Favor permits an empty-handed target.

   - Canonical fact: `FAV-01`
   - Evidence type: `human_decision`
   - Quote: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.” — page 2, “Wunsch”
   - Conflict: `legal_actions()` uses every player returned by `_others()` without checking their hand. `_resolve_effect()` silently does nothing when the selected hand is empty.
   - Expected: Empty-handed players are not legal Favor targets.

4. Pair theft permits an empty-handed target.

   - Canonical fact: `PAIR-01`
   - Evidence type: `human_decision`
   - Quote: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.” — page 2, “Pärchen”
   - Conflict: Pair actions target every living opponent returned by `_others()`; `_resolve_effect()` silently performs no theft for an empty hand.
   - Expected: Empty-handed players are not legal pair targets.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Deals 7 ordinary cards plus one Defuse; correct Kitten and extra-Defuse counts |
| Hidden setup information | Partially covered | Rendering hides other hands; full state still exposes them, which approved facts say cannot be fully verified |
| Normal turn flow | Covered | Zero or more plays followed by draw; living-player order is clockwise |
| Explosion and Defuse | Incorrect | Reinsertion choices and Attack continuation work, but voluntary explosion is exposed |
| Attack and Skip | Covered | Two owed turns, replacement Attack, and one-turn Skip consumption are represented |
| Named card effects | Covered | Favor choice, shuffle, and private top-three knowledge are modeled |
| Nope reactions | Covered | Cards are discarded, parity toggles cancellation, and responders act clockwise |
| Pair and triple combinations | Mostly covered | Transfer semantics work; pair target legality is too broad |
| Five-card combination | Incorrect | Post-discard retrieval set is not represented |
| Elimination and terminal result | Covered | Hand and Kitten are discarded; sole survivor receives `+1`, others `-1` |
| Empty deck/hand behavior | Covered by invariant | Empty hands can continue; implementation relies on the rulebook’s deck invariant |

## Missing deterministic scenarios

- A player draws a Kitten while holding a Defuse: verify `explode` is absent and every reinsertion position is available.
- Five distinct titles with an initially empty discard: verify a five-card action exists and each component title can be retrieved.
- Five distinct titles with a nonempty discard: verify retrieval includes both prior discard titles and newly discarded components.
- Favor against one empty-handed and one nonempty opponent: only the latter should be targetable.
- Pair theft against an empty-handed opponent: no pair action targeting that player should exist.
- An attacked player Defuses on the first owed turn: verify exactly one owed turn remains.
- A cancelled Attack during an owed turn: verify the original player remains active with the same obligation.

## Material questions for a human

None. The two major deviations are resolved by approved canonical facts and do not require further rulebook adjudication.

score: 0.76
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 2
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true