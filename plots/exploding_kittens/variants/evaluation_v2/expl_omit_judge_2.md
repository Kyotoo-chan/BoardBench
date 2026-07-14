## Assessment

`score: 0.72`  
`confidence: high`

The implementation correctly covers setup, normal turn progression, Attack obligations, Skip, Future, Shuffle, Favor donation, Nope chains, elimination, and returns. Two material mechanics contradict or omit approved facts: mandatory Defuse use and five-card combinations.

## Findings

### Major — Defuse can be declined

- Canonical fact: `DEF-01`
- Evidence type: `human_decision`
- Rule quote, page 2, “ENTSCHÄRFUNG”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Approved complete fact: if the player possesses a Defuse, it must be used; voluntary elimination is not offered.
- Conflicting transition: `legal_actions()` always adds `"explode"` during the `"defuse"` phase. `_apply_defuse()` passes that action to `_explode()`.
- Expected: a player holding Defuse must choose a legal reinsertion position and consume the Defuse.
- Implemented: the player may deliberately explode despite holding Defuse, potentially changing the winner.
- Severity: `major`

### Major — Five-distinct-card combinations and discard retrieval are absent

- Canonical facts: `FIVE-01`, `FIVE-02`, `COMBO-01`
- Evidence types:
  - `FIVE-01`: `rule_quote`
  - `FIVE-02`: `human_decision`
  - `COMBO-01`: `rule_quote`
- Rule quotes, page 2, “FÜNFLING”:
  - “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
  - “Wenn du eine Kombination spielst, gelten die Anweisungen auf den Karten nicht.”
- Approved complete facts: the five components enter the discard before retrieval; any card then present may be retrieved, including a just-discarded component or an Exploding Kitten. A retrieved Kitten stays harmless in hand and may participate in same-title combinations.
- Conflicting symbols: `legal_actions()` generates only singles, pairs, and triples. `_begin_card_action()` has no five-card branch or explicit discard-selection phase. `HAND_TITLES` also excludes `EXPLODING`.
- Expected: explicitly choose five distinct titles, open a Nope window, then explicitly select any current discard card for retrieval.
- Implemented: no five-card action or retrieval exists, and the state representation cannot hold a retrieved Kitten.
- Severity: `major`

### Question — Favor target becomes empty during reactions

- Canonical fact: `FAV-01`
- Rule quote, page 2, “WUNSCH”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
- Transition: `_resolve_pending()` silently does nothing if a valid Favor’s target used their last card as a Nope during the reaction chain.
- The packet decides that an initially empty player is not a legal target, but not what happens when an announced target becomes empty before an ultimately valid Favor resolves. This should be human-adjudicated, not scored as a contradiction.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and card counts | Covered | Deals 7 plus Defuse; correct Kittens and additional Defuses |
| Hands/deck visibility | Covered with limitation | `render()` hides identities appropriately; raw state remains inspectable |
| Ordinary turn flow | Covered | Zero or more plays followed by draw |
| Explosion/elimination | Covered | Hand and Kitten discarded; living-player order advances |
| Defuse | Incorrect | Reinsertion is explicit, but voluntary death is offered |
| Attack and Skip | Covered | Owed turns, replacement Attack, Defuse continuation, and elimination handling align |
| Future and Shuffle | Covered | Private top-three preview and deck-only shuffle |
| Favor | Mostly covered | Donor explicitly selects the transferred card |
| Nope chains | Covered | Out-of-turn responses toggle resolution; cancelled cards remain discarded |
| Pair and triple | Covered | Random pair theft and named triple request implemented |
| Five-card combination | Missing | No play or retrieval phase |
| Terminal result/returns | Covered | Sole survivor wins; `+1/-1` returns |
| Chance handling | Covered | Seeded shuffle and random pair theft |

## Missing deterministic scenarios

- A player draws a Kitten while holding Defuse: `"explode"` must not be legal.
- Defuse under Attack consumes exactly one owed turn.
- Five distinct titles retrieve a pre-existing discard card.
- Five distinct titles retrieve one of their own newly discarded components.
- Five distinct titles retrieve an Exploding Kitten without exploding.
- A hand-held Kitten participates in a same-title pair or triple.
- A Nope chain restores a five-card combination and still permits explicit retrieval.
- Favor’s target spends their final card as Nope before the Favor ultimately resolves, once human-adjudicated.

## Material human question

Should an ultimately valid Favor fizzle when its announced target spent their last card during the Nope window, or must some transfer obligation be preserved?

```text
score: 0.72
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```