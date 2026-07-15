## Assessment

**Score: 0.64 — confidence: high.** The core setup, turn progression, named-card effects, Attack debt, Defuse placement, elimination, and returns are mostly faithful. The score is reduced by three material legal-action deviations, particularly the complete omission of the five-card combination.

## Findings

### Major — Five-card combination is entirely absent

- **Canonical facts:** FIVE-01, FIVE-02, COMBO-01
- **Evidence type:** `rule_quote` and `human_decision`
- **Rule quote, page 2, “Fünfling”:** “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- **Additional quote, pages 1–2:** “Wenn du ein Exploding Kitten ziehst …” / “eine beliebige Karte aus dem Ablagestapel nehmen”
- **Conflicting code:** `Game.ASSUMPTIONS` explicitly says Fünfling is omitted; `Game.legal_actions()` and `Game.apply_action()` contain no five-card action or resolution.
- **Expected:** Five distinct titles are discarded, followed by an explicit choice of any card now in the discard. Under the approved decision, this can be one of the five newly discarded components or an Exploding Kitten; a retrieved Kitten remains harmless in hand.
- **Implemented:** No such action is ever legal or resolvable.

This removes a printed strategic option and discard-retrieval mechanism.

### Major — A player holding Defuse may voluntarily explode

- **Canonical fact:** DEF-01
- **Evidence type:** `human_decision`
- **Rule quote, page 2, “Entschärfung”:** “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- **Conflicting code:** In `Game.legal_actions()`, phase `exploding` always includes `Action("explode")` and additionally includes `Action("defuse")` when a Defuse is held. `Game.apply_action()` accepts either transition.
- **Expected:** The approved adjudication requires using a Defuse when one is available; voluntary elimination is not offered.
- **Implemented:** The player may select `exploding:explode`, discard their hand, and potentially determine the winner despite holding a Defuse.

This is a material terminal-rule deviation, although it does not prevent completion under a compliant policy.

### Major — Empty-handed players remain legal Favor and combination targets

- **Canonical facts:** FAV-01, PAIR-01, TRI-01
- **Evidence type:** `human_decision`
- **Rule quotes, page 2:**
  - “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
  - “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
- **Conflicting code:** `Game.legal_actions()` builds `opponents` from all living opponents without checking their hands, then emits Favor, pair, and triple actions against them. `_close_reaction()` resolves empty Favor/pair targets as no effect.
- **Expected:** Per the approved facts, empty-handed players are not legal Favor or pair targets; a triple inherits the pair targeting structure.
- **Implemented:** Players may legally discard one, two, or three cards against an empty target and receive nothing.

This introduces materially invalid choices that can waste cards and alter later survival.

### Minor — An Exploding Kitten cannot be requested with a triple

- **Canonical facts:** TRI-01, TRI-02
- **Evidence type:** `rule_quote`
- **Rule quote, page 2, “Drilling”:** “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst. Besitzt er solch eine Karte, muss er sie dir geben.”
- **Conflicting code:** `REQUESTABLE = tuple(c for c in CARD_TITLES if c != EXPLODING)` excludes Exploding Kitten from triple requests.
- **Expected:** No printed or approved restriction excludes a Kitten already held by the target from being the requested card.
- **Implemented:** Such a request can never be represented.

This is rare because Kittens enter hands only through discard retrieval, which is itself omitted.

## Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Setup and card counts | Covered | Correct player-dependent Kittens and Defuses |
| Normal turn flow | Covered | Zero-or-more plays followed by draw |
| Attack and Skip | Covered | Two-turn debt and one-turn Skip consumption represented |
| Explosion and Defuse | Partial | Reinsertion and debt handling work; voluntary explosion is illegal |
| See the Future / Shuffle | Covered | Private preview state and deck-only shuffle |
| Favor | Partial | Donation choice works; empty targets incorrectly legal |
| Nope chains | Covered | Cancellation parity and out-of-turn reactions represented |
| Pair and triple | Partial | Core transfers represented; targeting/request edge cases remain |
| Five-card combination | Missing | No legal action or resolution |
| Elimination and terminal result | Covered | Sole survivor and `+1/-1` returns correct |
| Private/chance information | Mostly covered | Seeded theft/shuffle and owner-specific preview data |
| Action serialization | Covered | Existing actions round-trip by name |

## Missing deterministic scenarios

- Drawing a Kitten while holding Defuse must expose only the mandatory Defuse path.
- Five distinct cards retrieve:
  - a pre-existing discard;
  - one of the five newly discarded components;
  - an Exploding Kitten, which remains harmless in hand.
- Favor, pair, and triple must reject empty-handed targets.
- A triple must be able to request an Exploding Kitten held by its target.
- A Defuse during the first of two Attack turns must end only that individual turn.
- A cancelled Attack must leave the original player in the same turn with no new turn debt assigned.
- Odd and even multi-Nope chains should respectively cancel and restore an underlying combination.

## Material questions for a human

None. The deviations above are decided by the approved facts; the unresolved physical timing of Nope reactions and shuffle/theft distributions does not require adjudication for these findings.

score: 0.64
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true