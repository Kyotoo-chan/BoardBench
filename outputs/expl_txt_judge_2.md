score: 0.68  
confidence: high

The core setup, draw loop, card effects, Attack obligations, elimination, terminal winner, and returns are substantially represented. Three material legal-action/transition contradictions remain, especially optionalizing mandatory Defuse.

## Findings

### Major 1 — A player may refuse an available Defuse

- Rulebook, page 2, “Entschärfung”: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Canonical fact `DEF-01` explicitly adjudicates this as mandatory when a Defuse is held.
- Code: `_legal_actions`, phase `"exploding"`, always includes `"accept:explode"` and additionally inserts `"use:defuse"` when available. `_apply_action` then permits `"accept:explode"` to call `_eliminate`.
- Expected: if the player possesses Defuse, their only resolution is to use it and choose a reinsertion position.
- Implemented: the player can voluntarily explode, potentially changing elimination order and the winner.

### Major 2 — Empty-handed players are legal Favor and pair targets

- Rulebook, page 2, “Wunsch”: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
- Rulebook, page 2, “Pärchen”: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Canonical facts `FAV-01` and `PAIR-01` specify that empty-handed players are not legal targets.
- Code: `_legal_actions` derives `opponents = _opponents(...)` solely from living status, then emits `play:favor:target:*` and `combo:pair:*:target:*` for every opponent. `_resolve_pending` silently produces no transfer when the selected target is empty.
- Expected: empty-handed opponents are omitted from those target-bearing actions.
- Implemented: players may discard Favor or a pair against an ineligible target for no result.

### Major 3 — Five-card retrieval can recover a component just played

- Rulebook, page 2, “Fünfling”: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Canonical fact `FIVE-01` adjudicates that the retrieved card must already have been in the discard before the combination was played.
- Code: `_apply_action` for `combo:five:*` first appends all five components to `result.discard`. After the Nope window, `_resolve_pending(kind="five")` enters `"take_discard"`, whose legal actions are generated from the now-expanded discard.
- Expected: retrieval choices are snapshotted from the pre-combination discard.
- Implemented: any of the five newly discarded titles can be immediately recovered. This also makes the combination yield a card when the discard was previously empty.

### Question 1 — Are single cat-card plays intended?

- Rulebook, page 2, “Katzen-Karten”: “Einzeln sind diese Karten machtlos.”
- Code: `NORMAL_PLAY_CARDS` includes all `CAT_CARDS`; playing one discards it, creates a `"noop"` pending effect, and opens a Nope window.
- The supplied materials do not clearly decide whether “machtlos” permits voluntarily playing/discarding one singly or only says it has no printed effect. This should be adjudicated rather than scored as an error.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and card counts | Covered | Correct 7 cards plus Defuse; correct Kittens and 2-player Defuses |
| Turn flow and drawing | Covered | Zero or more plays followed by draw; Skip/Attack end turns |
| Attack obligations | Covered | Two owed turns, replacement Attack, Skip consumption, Defuse continuation |
| Explosion and Defuse | Contradicted | Defuse can improperly be declined |
| Elimination and terminal result | Covered | Hand and Kitten discarded; sole survivor wins; correct returns |
| Favor | Partial | Donor chooses explicitly, but empty targets are exposed |
| Pair/triple | Partial | Transfers work; pair permits empty targets |
| Five-card combination | Contradicted | Retrieval pool includes newly played components |
| Nope reactions | Covered | Out-of-turn parity toggling and cancelled-card discard represented |
| See Future / Shuffle | Covered | Top three private view and deck-only shuffle |
| Hidden information | Partial | `render()` hides other hands and deck identities; raw state remains directly inspectable |
| Empty hand / deck count | Covered | Empty hands remain playable; render exposes deck size |

## Missing deterministic scenarios

- A player holding Defuse draws a Kitten: verify `"accept:explode"` is absent.
- Favor with a mixture of empty and nonempty opponents: verify only nonempty targets are legal.
- Pair with an empty opponent: verify that target is absent.
- Five-card combination with an initially empty discard: verify no newly played component can be retrieved.
- Five-card combination with a known pre-existing discard: verify exactly that prior pool remains selectable after the components are discarded.
- Defuse during the first of two Attack turns: verify reinsertion ends only that individual turn.
- Cancelled Attack during an owed turn: verify the same player continues with the unchanged obligation.
- Adjudicated test for whether a single cat card may be played.

## Material questions for a human

- Does “Einzeln sind diese Karten machtlos” allow a cat card to be played singly as an actionless discard?
- Should the public API provide player-specific observations rather than exposing `hands` and `deck` as public `GameState` fields? The canonical facts acknowledge that secrecy is not fully verifiable under the minimal API.

score: 0.68
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true