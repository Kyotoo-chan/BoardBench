Score: 0.88  
Confidence: high

The implementation captures setup, normal turn flow, Attack/Skip obligations, Defuse reinsertion, elimination, terminal returns, combinations, and deterministic Nope reactions well. The main clear deviation is that empty-handed opponents remain selectable for Favor and pair/triple actions. A separate legal sequence can exhaust the deck after retrieving a discarded Kitten, but the canonical material does not specify how that state should resolve.

## Findings

### Major — Empty-handed opponents are offered as theft targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`, `TRI-01`
- Evidence type: `human_decision`
- Rulebook quotes, page 2:
  - Favor: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
  - Pair: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
  - Triple: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
- Approved complete expectations:
  - `FAV-01`: empty-handed players are not legal targets.
  - `PAIR-01`: empty-handed players are not legal targets.
  - `TRI-01` inherits the pair procedure apart from naming the requested card.
- Conflicting symbols/transitions:
  - `Game.legal_actions()`
  - `_other_alive()`
  - `_resolve_pending()` branches for `"Auswahl"`, `"pärchen"`, and `"drilling"`
- Expected: target-bearing Favor, pair, and triple actions should only name living opponents with at least one card.
- Implemented: actions are generated for every other living player regardless of hand size. Favor and pair silently do nothing against an empty hand; triple likewise remains selectable and cannot transfer anything.

This materially expands the legal action space and can waste cards on targets explicitly excluded by approved adjudication.

### Question — Legal Kitten retrieval can lead to an undefined empty-deck crash

- Related fact IDs: `FIVE-01`, `FIVE-02`, `TURN-04`, `TERM-01`
- Evidence type: `human_decision` for Kitten retrieval; printed rule is internally incomplete for the resulting state.
- Rulebook quotes:
  - Page 2: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
  - Page 1: “Du beendest deinen Zug, indem du die oberste Karte vom Spielstapel ziehst.”
  - Page 1, Spielende: “Keine Sorge, der Spielstapel wird nie leer, weil alle Spieler (außer einem) vorher Exploding Kittens ziehen werden – Explosionen garantiert!”
- Relevant symbols:
  - `_resolve_pending()` correctly permits a five-card combination to retrieve `GEFAHR`.
  - `_draw()` raises `RuntimeError` when `state.deck` is empty.
- Implemented: a discarded Kitten can legally move into a player’s hand. That may leave too few Kittens in the draw pile to eliminate all but one player, eventually reaching the runtime exception.
- Missing expected behavior: the approved packet does not decide how an empty pile should resolve after this legal retrieval, so the exception cannot be scored as a clear rule contradiction.

### Question — Single symbol cards may be discarded for no effect

- Related text: page 2, Katzen-Karten: “Einzeln sind diese Karten machtlos …”
- Conflicting symbol: the symbol-card titles are included in `PLAYABLE`, and `_resolve_pending()` deliberately gives them no individual effect.
- Ambiguity: “machtlos” could mean that a single card may be played but does nothing, or that it has no valid individual play. The approved facts do not settle this, so no code change is scored as mandatory.

## Coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Setup | Full | Correct deal, starting Defuses, player-minus-one Kittens, and two-player Defuse exception |
| Normal turn flow | Full | Zero-card pass represented by immediate draw; repeated pre-draw plays supported |
| Attack and Skip | Full | Owed turns, Attack replacement, and one-turn Skip consumption are correct |
| Draw and Defuse | Full | Forced Defuse, explicit secret-position choice, and relative deck order preserved |
| Elimination/terminal | Full | Hand and Kitten discarded; remaining Attack obligation removed; sole survivor and returns correct |
| Favor | Partial | Donor explicitly chooses; empty-handed targets incorrectly legal |
| Pair/triple | Partial | Random theft/request behavior correct; empty-handed targets incorrectly legal |
| Five-card combination | Full | Distinct titles discarded first; self-retrieval and Kitten retrieval correctly supported |
| Nope reactions | Full | Out-of-turn opportunities, toggling, discard retention, and continued actor turn modeled |
| Preview/shuffle | Full | Private top-three record and deck-only shuffle represented |
| Chance | Full | Seeded setup, shuffle, and random pair theft |
| Private information | Partial | Rendering hides non-current hands and preview data, but there is no player-specific observation interface |
| Empty-deck behavior | Undefined | Legal Kitten retrieval exposes a rulebook gap and implementation exception |

## Missing deterministic scenarios

- Favor must omit an empty-handed living opponent from legal targets.
- Pair must omit an empty-handed living opponent.
- Triple target legality should be explicitly tested after confirming that it inherits the pair restriction.
- Favor donation should restore control to the original actor after the donor chooses a card.
- A five-card combination should retrieve one of its own newly discarded components.
- A five-card combination should retrieve a discarded Kitten into hand without exploding.
- A retrieved Kitten should participate in a pair or triple without executing its printed effect.
- Retrieve enough discarded Kittens to exhaust the deck while multiple players remain, documenting the unresolved outcome.
- Nope an Attack while the actor already owes two turns; confirm the actor continues the same owed turn.
- Defuse during an attacked turn; confirm exactly one owed turn ends and the remaining one continues.

## Material questions for a human

1. What should happen if the draw pile becomes empty while multiple players remain after one or more discarded Kittens have been retrieved?
2. Does “Einzeln sind diese Karten machtlos” permit a single cat/symbol card to be discarded as a no-effect play?
3. Should the approved empty-hand target restriction be stated explicitly for triples, or is “Wie ein Pärchen” sufficient to inherit it?

score: 0.88
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true