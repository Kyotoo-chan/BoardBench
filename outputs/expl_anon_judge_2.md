score: 0.64  
confidence: high

The core setup, normal turn loop, Attack/Skip obligations, card effects, elimination, terminal detection, and returns are substantially represented. Three explicit rule conflicts permit illegal choices or materially incorrect combination behavior.

## Findings

### Major 1 — Defuse use is incorrectly optional

- Rulebook, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine ‚Entschärfung‘ ausspielen, statt zu sterben.”
- Approved fact `DEF-01` resolves this choice: if the player has a Defuse, it must be used; voluntary elimination is not offered.
- Code: `legal_actions()` line 196 always includes `"explode"` during the `defuse` phase, then adds `"defuse:use-protection"` when available. `apply_action()` line 298 eliminates the player if `"explode"` is selected.
- Expected: a player holding Defuse has only the Defuse action followed by reinsertion.
- Implemented: the player may voluntarily explode, potentially changing the winner.

### Major 2 — Five-card combinations can retrieve one of their own components

- Rulebook, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Approved fact `FIVE-01`: “The selected card must already have been in the discard before playing the combination.”
- Code: `legal_actions()` lines 256–257 deliberately computes `set(state.discard).union(chosen)`, making newly selected combination cards recoverable. `_resolve_pending()` lines 545–548 then removes that card from the discard and returns it.
- Expected: recovery choices come exclusively from the pre-existing discard pile.
- Implemented: even with an empty discard pile, a five-card combination can recover one of its just-played cards.

### Major 3 — Empty-handed players are legal Favor and Pair targets

- Rulebook, page 2, “Wunsch”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
- Rulebook, page 2, “Pärchen”: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Approved facts `FAV-01` and `PAIR-01` explicitly state that empty-handed players are not legal targets.
- Code: `other_players` at lines 220–224 filters only for living non-actors. Those targets are used for Favor and Pair at lines 226–238 without checking hand size. Resolution at lines 513–531 silently turns the action into a no-op if the target is empty.
- Expected: empty-handed targets are excluded from those legal actions.
- Implemented: the actor may discard a Favor or pair against an empty hand and receive nothing.

### Minor 1 — An Exploding Kitten cannot be requested with a triple

`REQUESTABLE` at line 39 excludes `EXPLODING`. Approved facts allow a retrieved Kitten to remain in a hand, while `TRI-01` describes requesting a named card without excluding that title. This removes a rare but potentially valid request when another player holds a retrieved Kitten.

### Question 1 — Legal Kitten retrieval can make the draw pile exhaustible

Page 1, “Spielende” says: “Keine Sorge, der Spielstapel wird nie leer, weil alle Spieler (außer einem) vorher Exploding Kittens ziehen werden.”

Approved facts nevertheless allow a five-card combination to retrieve an Exploding Kitten from the discard and retain it in hand. In a game with at least three players, this can remove an already-triggered Kitten from circulation while multiple players remain. `_draw()` lines 557–561 then raises `RuntimeError` if the deck becomes empty.

The packet does not specify the correct result for this newly possible empty-deck state. A human ruling is needed rather than treating one resolution as canonical.

## Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Setup and card counts | Covered | Correct for 2–5 players, including two-player Defuse variant |
| Normal turn flow | Covered | Zero or more plays followed by draw |
| Attack and Skip | Covered | Owed turns, replacement Attack, and one-turn Skip behavior align |
| Explosion and Defuse | Partial | Reinsertion works; illegal voluntary explosion exists |
| Elimination and winner | Covered | Hand/Kitten discarded; sole survivor and returns correct |
| Preview and Shuffle | Covered | Top-three preview and deck-only shuffle represented |
| Favor | Partial | Recipient chooses card; empty targets incorrectly legal |
| Nope reactions | Covered | Out-of-turn chain and toggling are represented |
| Pair and Triple | Partial | Core effects work; empty Pair targets and Kitten requests differ |
| Five-card combination | Partial | Distinct titles supported; recovery pool is incorrect |
| Private information | Partial | Rendering hides other hands, but there is no full player-observation boundary |
| Empty-deck behavior | Unresolved | Canonical facts permit a state the printed rulebook says cannot occur |

## Missing deterministic scenarios

- A player with Defuse draws a Kitten and cannot choose explosion.
- Favor and Pair legal-action sets exclude an empty-handed target.
- Five distinct cards with an empty discard offer no valid recovery action.
- Five distinct cards can recover only cards present before the combination.
- A triple can request a Kitten held after discard retrieval.
- Defuse during each of two Attack-owed turns consumes exactly one owed turn.
- Attack played during an owed turn replaces the remaining obligation with exactly two turns for the next player.
- A Nope/Nope chain alternately cancels and restores each named effect.
- Elimination during Attack removes the eliminated player’s remaining owed turns.
- Three-or-more-player sequence involving Kitten recovery followed by draw-pile exhaustion.

## Material questions for a human

- What should happen if retrieving an Exploding Kitten makes the draw pile empty while multiple players remain?
- Should the benchmark require a formal player-specific observation API, or is private rendering sufficient for hand and reinsertion secrecy?

score: 0.64
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true