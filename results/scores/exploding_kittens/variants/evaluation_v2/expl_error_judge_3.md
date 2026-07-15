score: 0.50  
confidence: high

The setup, ordinary turn flow, most card effects, combinations, terminal detection, and returns are represented well. However, Attack/Skip turn debt is materially incorrect, mandatory Defuse use is not enforced, and retrieving an Exploding Kitten via a five-card combination incorrectly triggers an explosion.

## Findings

### Major

1. A normal Attack assigns three turns instead of two.

- Canonical fact: `ATK-01`
- Evidence type: `rule_quote`
- Rulebook quote, page 2, “Angriff”: “Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.”
- Conflicting code: `_resolve_pending`, `kind == ATTACK`, normal branch sets the next player and `state.turn_debt = 3`.
- Expected: the next living player owes exactly two turns.
- Implemented: the next player owes three turns.

2. An Attack played while under Attack neither transfers play correctly nor replaces the remaining obligation.

- Canonical fact: `ATK-02`
- Evidence type: `human_decision`
- Rulebook quote, page 2, “Angriff”: “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Conflicting code: `_resolve_pending`, `kind == ATTACK`, `state.turn_debt > 1` branch only executes `state.turn_debt += 1`; it does not advance `active_player`.
- Expected: the attacking victim immediately ceases being active, and the following living player owes exactly two turns.
- Implemented: the same player remains active and their existing debt increases, commonly from two to three.

3. One Skip incorrectly cancels every outstanding attacked turn.

- Canonical fact: `SKIP-02`
- Evidence type: `rule_quote`
- Rulebook quote, page 2, “Hops!”: “Falls du „Hops!“ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal „Hops!“ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `_resolve_pending`, `kind == SKIP`, always advances to `_next_alive(...)` and resets `turn_debt = 1`.
- Expected: one Skip consumes exactly one owed turn; if another is owed, the attacked player remains active for it.
- Implemented: one Skip removes all remaining debt and passes play onward.

4. A player holding a Defuse may voluntarily decline it and be eliminated.

- Canonical fact: `DEF-01`
- Evidence type: `human_decision`
- Rulebook quote, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Conflicting code: `legal_actions` in phase `"defuse"` always includes `"defuse:decline"`; `_apply_defuse` accepts it and eliminates the player regardless of whether their hand contains a Defuse.
- Expected: under the approved human decision, a held Defuse must be used; decline is legal only when none is held.
- Implemented: voluntary elimination remains available even with one or more Defuses.

5. Retrieving an Exploding Kitten from the discard wrongly initiates Defuse/elimination instead of putting it into the hand.

- Canonical facts: `FIVE-01`, `FIVE-02`
- Evidence type: `human_decision`
- Rulebook quotes:
  - Page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
  - Page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Conflicting code: `_resolve_pending`, `kind == "five"`, removes the selected Kitten from the discard and sets `state.phase = "defuse"` when `recovered == EXPLODING`.
- Expected: discard retrieval is not a draw; the Kitten enters the actor’s hand without exploding and may later participate in same-title combinations.
- Implemented: retrieval triggers the Defuse phase and can consume a Defuse or eliminate the player.

### Minor

6. Empty-handed players remain legal Favor and pair targets.

- Canonical facts: `FAV-01`, `PAIR-01`
- Conflicting code: `legal_actions` uses `_other_alive`, which checks only whether targets are alive, for both `play:wunsch:target:*` and `pair:*:target:*`.
- Expected: empty-handed players are excluded from the legal target list.
- Implemented: such actions are legal and resolve without transferring or stealing a card.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Deals seven plus one Defuse; inserts correct Kittens and extra Defuses. |
| Hidden hands/deck | Mostly covered | Rendering exposes only the current decision-maker’s hand and private preview. |
| Normal turn flow | Covered | Zero or more plays followed by draw is supported. |
| Attack obligations | Contradicted | Normal and counter-Attack debt are wrong. |
| Skip | Contradicted under Attack | Ordinary Skip works; attacked Skip clears excessive debt. |
| Explosion/Defuse | Contradicted | Resolution works structurally, but mandatory Defuse use is not enforced. |
| Elimination/terminal result | Covered | Hand and Kitten are discarded; sole survivor receives `+1`. |
| Favor | Mostly covered | Donation is target-selected; empty targets are erroneously legal. |
| Shuffle/Future | Covered | Shuffle affects the deck; preview shows up to three privately. |
| Nope chains | Covered | Out-of-turn toggling and discarded cancelled cards are represented. |
| Pair/triple | Mostly covered | Effects work; pair target filtering is incomplete. |
| Five-card combination | Contradicted for Kitten | Self-component retrieval is allowed, but Kitten retrieval explodes. |
| Returns | Covered | Nonterminal zeroes and terminal `+1/-1` match the convention. |

## Missing deterministic scenarios

- A normal Attack leaves the next player with exactly two turns.
- Attack during an attacked turn immediately transfers exactly two turns to the following player.
- One Skip under Attack consumes one turn while leaving the second owed.
- Two Skips consume both attacked turns.
- Defuse phase offers no decline action when a Defuse is held.
- Five-card retrieval places an Exploding Kitten into hand without entering Defuse phase.
- Five-card retrieval may select one of the five newly discarded components.
- Empty-handed players are absent from Favor and pair target actions.
- Defusing the first of two attacked turns leaves the player owing the second.
- Elimination during an attacked turn discards the remaining debt.

## Material questions for a human

None. The approved facts decide the material deviations above. Exact physical Nope timing and verification of secret information remain intentionally outside hard scoring.

score: 0.50
confidence: high
critical_issues: 0
major_issues: 5
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true