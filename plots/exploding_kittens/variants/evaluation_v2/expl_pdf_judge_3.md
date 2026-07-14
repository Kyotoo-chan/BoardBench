Score: **0.54**, confidence: **high**. Setup, ordinary turn progression, Attack/Skip obligations, Defuse, elimination, returns, and most information handling are sound. However, advertised combination actions can crash, and five-card retrieval contradicts the corrected approved fact.

## Findings

### Critical — Cat-card combinations can crash

- Canonical fact IDs: `PAIR-01`, `TRI-01`, `FIVE-01`
- Evidence type: `rule_quote`
- Rulebook quotes, page 2, “Kombinationen”:
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
  - “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
  - “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Conflicting code: `CAT_CARDS`, `GameState.legal_actions()`, and `GameState._play_combo()`.
- Expected: Cat-card titles must work in pairs, triples, and five-card combinations like every other title.
- Implemented: Cat identifiers contain colons, such as `cat:taco`, but `_play_combo()` parses actions using fixed positions from `action.split(":")`. For example, the legal action `combo:pair:cat:taco:target:player1` causes the target parser to process `"target"` as an integer and raise `ValueError`. Five-card actions containing cat titles are similarly misparsed and may remove the wrong card or crash.
- Impact: Common, rules-legal actions returned by `legal_actions()` can terminate execution.

### Major — Five-card combinations cannot reliably retrieve their own components

- Canonical fact ID: `FIVE-01`
- Evidence type: `human_decision`
- Rulebook quote: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” Page 2, “Kombinationen — Fünfling.”
- Conflicting code: five-card generation in `GameState.legal_actions()`:
  - requires `self.discard` to be nonempty;
  - constructs retrieval choices only from the pre-play contents of `self.discard`.
- Expected: The five cards enter the discard before retrieval, so any one of those components may immediately be retrieved. This remains legal even if the discard was empty before playing the combination.
- Implemented: A component is offered only when a card with the same title was already in the discard. No five-card action is offered at all when the discard starts empty. `_resolve_effect()` could retrieve a newly discarded component, but the required action can never be selected through the legal-action interface.
- Impact: A material approved combination outcome is absent.

### Major — Empty-handed players remain legal Favor and pair targets

- Canonical fact IDs: `FAV-01`, `PAIR-01`
- Evidence type: `human_decision`
- Rulebook quotes, page 2:
  - Favor: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
  - Pair: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Conflicting code: `GameState._opponents()` returns every living opponent without checking their hand; `legal_actions()` uses it for Favor and pair targets. `_resolve_effect()` then silently makes either action ineffective when the target is empty.
- Expected: Under the approved decisions, empty-handed players are not legal targets.
- Implemented: They are selectable targets and the spent card or pair resolves as a no-op.
- Impact: The legal-action set permits materially invalid card expenditure and transition outcomes.

### Question — Empty draw pile after retrieving discarded Kittens

Page 1 says: “Keine Sorge, der Spielstapel wird nie leer, weil alle Spieler (außer einem) vorher Exploding Kittens ziehen werden – Explosionen garantiert!”

However, approved fact `FIVE-02` permits taking a discarded Exploding Kitten into a hand without exploding. This can remove Kittens from the draw-pile/elimination cycle on which that assurance relies. If legal retrievals eventually leave multiple players alive with an empty deck, `_draw()` raises `RuntimeError`.

The packet does not specify the correct outcome for this adjudication-created edge case. A human decision is needed before treating the exception as a code contradiction.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Setup and card counts | Matches `SET-01`–`SET-09`, including the two-player Defuse variant |
| Normal turn flow | Draw/pass/multiple-play flow and clockwise advancement match |
| Attack, Skip, Defuse | Owed-turn replacement, consumption, and elimination clearing appear correct |
| Favor and pair targeting | Incorrect for empty-handed targets |
| Nope reactions | Toggle, discard, cancellation, and continued turn appear consistent |
| See the Future / Shuffle | Private preview and deck-order changes appear consistent |
| Combinations | Pair/triple/five parsing can crash; five-card retrieval choices are incomplete |
| Elimination and terminal result | Hand/Kitten discard, sole survivor, and `+1/-1` returns match |
| Private information | Hands and previews are hidden from the current non-owner rendering view |
| Exceptional deck exhaustion | Undecided by the approved facts |

## Missing deterministic scenarios

Scenarios that should be added or retained:

- Apply a cat-title pair action returned by `legal_actions()`.
- Apply a cat-title triple, including a cat-title request.
- Apply five-card combinations containing cat identifiers in different positions.
- Retrieve one of the five just-discarded components when the discard was initially empty.
- Retrieve a just-discarded component when other cards were already discarded.
- Verify that empty-handed players are excluded from Favor and pair targets.
- Exercise a five-card retrieval of an Exploding Kitten followed by possible deck exhaustion.
- Verify Attack replacement, two consecutive Skips, and Defuse during the first of two owed turns.
- Verify even and odd Nope chains around cards and combinations.

## Material question for a human

When five-card retrieval places enough Exploding Kittens into players’ hands that the draw pile becomes empty while multiple players remain alive, should drawing be impossible, should the game terminate, or should another rule-specific recovery occur?

score: 0.54
confidence: high
critical_issues: 1
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true