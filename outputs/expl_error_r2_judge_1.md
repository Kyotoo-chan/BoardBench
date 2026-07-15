score: 0.58  
confidence: high

The implementation covers setup, ordinary turns, Attack chaining, Nope reactions, information hiding, elimination, terminal returns, and most named-card effects. However, five material transition/legal-action errors can alter player elimination, turn order, or card ownership. No issue appears severe enough to prevent ordinary games from completing reliably.

## Findings

### Major 1 — Skip incorrectly clears the entire remaining Attack obligation

- Canonical fact ID: `SKIP-02`
- Evidence type: `rule_quote`
- Rulebook, page 2, “Hops!”: “Falls du „Hops!“ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal „Hops!“ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `Game._settle_pending`, `kind == "skip"` transition.
- Expected: When `turns_left == 2`, one Skip consumes one individual turn and leaves the attacked player owing one more turn.
- Implemented: `_advance_to(s, self._next_alive(s, actor), 1)` immediately advances to the next player, discarding the second owed turn.

This materially weakens Attack and changes turn order in a common interaction.

### Major 2 — A player holding Defuse may voluntarily explode

- Canonical fact ID: `DEF-01`
- Evidence type: `human_decision`
- Rulebook, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Approved decision: If the player has a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting code: `Game.legal_actions`, `phase == "defuse"`, and `Game.apply_action`.
- Expected: With a Defuse in hand, the legal choice is to play it and proceed to secret reinsertion.
- Implemented: `explode:voluntarily` remains legal alongside `react:Entschärfung`; selecting it calls `_eliminate`.

This can directly change the winner and terminal returns.

### Major 3 — Five-card combinations generally cannot retrieve a just-discarded component

- Canonical fact ID: `FIVE-01`
- Evidence type: `human_decision`
- Rulebook, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Approved decision: The five components enter the discard before retrieval, so any one of them may be retrieved immediately.
- Conflicting code: `Game.legal_actions`, five-card action generation.
- Expected: A player with five distinct titles can choose any card that will be in the discard after playing them, even if the discard was previously empty.
- Implemented: Five-card actions require `state.discard` to be nonempty and derive `takeable` solely from the pre-action discard. A component title is selectable only if that title was already present there.

The later `_settle_pending` logic can remove a recently played component, but the legal-action generator usually provides no action selecting it.

### Major 4 — Retrieving an Exploding Kitten from the discard causes an explosion

- Canonical fact ID: `FIVE-02`
- Evidence type: `human_decision`
- Rulebook, pages 1–2: “Wenn du ein Exploding Kitten ziehst …” / “eine beliebige Karte aus dem Ablagestapel nehmen”
- Approved decision: Taking a Kitten from the discard is not drawing it from the draw pile. It stays safely in hand and does not trigger Defuse or elimination.
- Conflicting code: `Game._settle_pending`, `kind == "five"` with `wanted == EXPLODING`.
- Expected: Remove the Kitten from the discard and add it to the actor’s hand.
- Implemented: The code sets `phase = "defuse"` without adding the Kitten to the hand. The player must then Defuse or explode as though the Kitten had been drawn.

If the player Defuses, the retrieved Kitten is improperly reinserted into the deck; if they do not, elimination incorrectly occurs.

### Major 5 — Empty-handed players are legal Favor and Pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rulebook, page 2:
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved decisions: Empty-handed players are not legal targets for either action.
- Conflicting code: `Game.legal_actions` builds `others` from living players without checking their hands; `_settle_pending` silently produces no effect when the selected target is empty.
- Expected: Favor and Pair actions should list only opponents holding at least one card.
- Implemented: Players may discard Favor or a pair against an empty target and receive nothing.

This materially changes action legality and permits otherwise forbidden card expenditure.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and card counts | Pass | Seven dealt cards plus one Defuse; correct Kitten and extra-Defuse counts |
| Hand/deck privacy | Pass | Render hides other hands and Future knowledge |
| Ordinary turn flow | Pass | Zero or more plays followed by draw |
| Attack | Mostly pass | Two turns and replacement Attack work; attacked Skip is wrong |
| Skip | Fail | Does not preserve the second owed Attack turn |
| Explosion/Defuse | Fail | Voluntary elimination is exposed |
| Favor and Pair | Fail | Empty targets are accepted |
| Triple | Pass | Requested title transfers only when held |
| Five-card combination | Fail | Component retrieval and Kitten retrieval are wrong |
| Nope chain | Pass | Cancellation toggles and cards remain discarded |
| Shuffle/Future | Pass | Deck-only shuffle and private top-three preview |
| Elimination | Pass | Hand and Kitten discarded; owed Attack turns disappear |
| Terminal state/returns | Pass | Immediate sole-survivor terminal state and `+1/-1` returns |

## Missing deterministic scenarios

Recommended deterministic scenarios:

1. An attacked player owes two turns and plays exactly one Skip.
2. A player draws a Kitten while holding a Defuse and cannot choose elimination.
3. Five distinct cards are played while the discard was initially empty; one component is retrieved.
4. A five-card combination retrieves an Exploding Kitten, which remains safely in hand.
5. Favor and Pair action enumeration with one empty-handed opponent.
6. Defuse during the first of two attacked turns, confirming that the second turn remains.
7. Attack played during an Attack, confirming replacement with exactly two turns for the following player.
8. Elimination during an Attack, confirming that the eliminated player’s remaining obligation disappears.

## Material questions for a human

None for the scored findings. Each conflict is resolved by an approved canonical fact or explicit human decision.

```text
score: 0.58
confidence: high
critical_issues: 0
major_issues: 5
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```