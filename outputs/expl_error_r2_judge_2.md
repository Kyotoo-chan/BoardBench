score: 0.55, confidence: high. The module implements setup, ordinary draws, most cards, reactions, elimination, terminal returns, and information hiding reasonably well. However, five material rule/action contradictions remain. None appears to make ordinary play universally impossible, so I found no critical issue.

## Findings

### Major 1 — Skip incorrectly cancels every remaining attacked turn

- Canonical fact ID: `SKIP-02`
- Evidence type: `rule_quote`
- Quote, page 2, “Hops!”: “Falls du „Hops!“ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal „Hops!“ ausspielen, um beide Züge zu beenden.”
- Conflicting code: `Game._settle_pending()`, `kind == "skip"` calls `_advance_to(..., 1)` unconditionally.
- Expected: When `turns_left == 2`, one Skip ends only the current owed turn. The attacked player remains current with one turn still owed.
- Implemented: The game advances immediately to the next player and clears the attacked player’s entire obligation.

### Major 2 — Defuse is optional despite the binding human decision

- Canonical fact ID: `DEF-01`
- Evidence type: `human_decision`
- Quote, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Approved decision: If the player has a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting code: `Game.legal_actions()`, phase `"defuse"`, always includes `"explode:voluntarily"`.
- Expected: A player holding Defuse has only the Defuse response.
- Implemented: The player may decline Defuse and eliminate themselves, potentially changing the winner.

### Major 3 — Retrieving a discarded Kitten incorrectly triggers an explosion

- Canonical fact ID: `FIVE-02`
- Evidence type: `human_decision`
- Quotes:
  - Page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst …”
  - Page 2, “Fünfling”: “eine beliebige Karte aus dem Ablagestapel nehmen”
- Approved decision: Taking a Kitten from the discard is not drawing it. It remains safely in hand and may participate in combinations.
- Conflicting code: `Game._settle_pending()`, `kind == "five"` branches on `wanted == EXPLODING` and changes to phase `"defuse"` without adding the Kitten to the hand.
- Expected: Remove the Kitten from the discard and add it to the actor’s hand without explosion.
- Implemented: Retrieval initiates Defuse/elimination processing as though the Kitten were drawn.

### Major 4 — Five-card combinations cannot retrieve newly discarded components in all permitted states

- Canonical fact ID: `FIVE-01`
- Evidence type: `rule_quote`
- Quote, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Conflicting code: `Game.legal_actions()` requires `state.discard` to be nonempty and constructs `takeable` solely from the discard before the five components are played.
- Expected: The five cards enter the discard before retrieval. A player may therefore retrieve one of those components, even if the discard was previously empty.
- Implemented:
  - No five-card action is available when the discard starts empty.
  - A component title absent from the old discard cannot be selected, even though playing the combination puts it there.

The settlement logic can retrieve a newly played matching component, but the legal-action generator frequently prevents selecting it.

### Major 5 — Empty-handed players are exposed as legal Favor and Pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Quotes, page 2:
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved decisions: Empty-handed players are not legal targets for either action.
- Conflicting code: `Game.legal_actions()` builds `others` from every other living player without checking their hand and uses it for Favor and Pair actions.
- Expected: Only living opponents with at least one card appear as targets.
- Implemented: Empty-handed opponents remain legal targets; settlement then silently makes the action ineffective.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Setup and card counts | Covered |
| Hidden hands/deck size | Substantially covered |
| Ordinary play and mandatory draw | Covered |
| Attack | Mostly covered |
| Skip under Attack | Contradicted |
| Explosion and Defuse | Voluntary-elimination defect |
| Future and Shuffle | Covered |
| Favor and Pair | Invalid empty targets |
| Triple | Covered |
| Five-card combination | Material legality/retrieval defects |
| Nope chains | Covered |
| Elimination and terminal result | Covered |
| Returns | Covered |
| Private observation | Render hides other hands; full verification remains limited |

## Missing deterministic scenarios

- One Skip during a two-turn Attack leaves the same player owing one turn.
- Two Skips consume both attacked turns.
- A player holding Defuse cannot choose elimination.
- Five distinct cards can be played with an initially empty discard and retrieve one component.
- Every newly discarded component is selectable during five-card retrieval.
- A retrieved Exploding Kitten enters the hand without opening a Defuse phase.
- Empty-handed opponents are absent from Favor and Pair targets.
- An eliminated attacked player’s remaining turn debt disappears.
- Odd and even Nope chains respectively cancel and restore an action.

## Material question for a human

Retrieving Exploding Kittens can eventually leave the draw pile empty while multiple players remain alive. The approved facts permit retrieval but do not define what happens when a mandatory draw is attempted from an empty pile. `apply_action("draw")` would currently crash at `deck.pop(0)`. This should remain an unscored clarification question unless the intended outcome is adjudicated.

score: 0.55
confidence: high
critical_issues: 0
major_issues: 5
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true