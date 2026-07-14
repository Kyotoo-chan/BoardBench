score: 0.62  
confidence: high

The setup, ordinary turn cycle, attacks, Defuses, elimination, terminal returns, and most named-card effects closely follow the approved facts. The score is reduced primarily because several explicitly legal Cat-card combinations can crash or partially mutate the state, while empty-handed players are incorrectly offered as targets.

## Findings

### Critical — Cat-card combinations use an ambiguous action encoding and can crash

Rulebook evidence, page 2, “Kombinationen”:

- Pärchen: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”
- Drilling: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
- Fünfling: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”

Conflicting code:

- Cat titles contain colons, such as `cat:taco`.
- `legal_actions()` constructs actions such as `combo:pair:cat:taco:target:player1` at `implementation.py:124`.
- `_play_combo()` parses every action with `parts = action.split(":")` at `implementation.py:330`, then assumes fixed indexes at lines 332–367.

Expected behavior:

- A pair or triple of any same-title Cat card must resolve normally.
- A five-card combination containing a Cat title must discard exactly the selected five cards and enter the reaction/effect flow.

Implemented behavior:

- For `combo:pair:cat:taco:target:player1`, `parts[4]` is `"target"`, so `int(parts[4].removeprefix("player"))` raises `ValueError`.
- Cat triples fail similarly.
- Five-card combinations containing Cat titles are parsed into truncated or nonexistent card names. They can raise after some earlier components have already been discarded, leaving a partially mutated state.

Because Cat cards are expressly intended for combinations and occupy a large part of the supplied deck, this creates a common exception path from actions that the module itself reports as legal.

### Major — Empty-handed players are illegally targetable by Favor and pairs

Rulebook evidence, page 2:

- Wunsch: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.”
- Pärchen: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.”

The approved FAV-01 and PAIR-01 expectations explicitly adjudicate that empty-handed players are not legal targets.

Conflicting code:

- `_opponents()` returns every living opponent without considering hand size.
- `legal_actions()` uses that result for Favor at lines 112–114 and pairs at lines 121–125.
- `_resolve_effect(FAVOR)` silently does nothing when the target is empty at lines 392–395.
- `_resolve_effect("pair")` likewise performs no theft when the target is empty.

Expected behavior:

- Favor and pair actions targeting an empty-handed opponent must be absent from `legal_actions()`.

Implemented behavior:

- They are advertised as legal.
- After the reaction window, the actor loses the played card or pair and receives nothing.

This materially changes legal play and can waste cards through a choice that canonical facts prohibit.

### Question — Observation boundaries do not establish full secrecy

Rulebook evidence:

- Page 1, setup: “Halte dein Blatt stets verdeckt.”
- Page 2, Blick in die Zukunft: “Zeige diese Karten bloß nicht deinen Mitspielern.”

`render()` hides opponents’ hands and only shows a preview to `peek_actor`, which is appropriate. However, `GameState.hands`, `GameState.deck`, `peek_cards`, and secret Defuse insertion actions remain directly accessible to any caller holding the state.

The approved facts already note that secrecy cannot be fully verified without player-specific observations. Whether direct state access constitutes player-visible information therefore depends on the intended API boundary and should not be scored as a definite code failure from this packet alone.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and card counts | Pass | Correct initial Defuses, seven ordinary cards, player-count Kittens, and two-player variant |
| Private setup information | Question | `render()` hides hands; raw state does not |
| Normal turn flow | Pass | Zero or more plays followed by draw |
| Attack and owed turns | Pass | Attack replaces obligations; Skip/Defuse consume one owed turn |
| Explosion and Defuse | Pass | Mandatory Defuse, explicit insertion, correct elimination |
| Named card effects | Pass | Favor targeting exception noted above |
| Nope reactions | Pass | Clockwise pass opportunities and toggle behavior represented |
| Pair/triple/five combinations | Fail | Colon-bearing Cat titles break parsing |
| Empty-hand targeting | Fail | Favor and pair expose prohibited targets |
| Terminal condition | Pass | Immediate sole-survivor winner |
| Returns | Pass | Nonterminal zero; terminal `+1/-1` |

## Missing deterministic scenarios

Recommended deterministic scenarios not evidenced by this packet:

1. Apply a legal pair action for each `cat:*` title and verify no exception and one random transfer.
2. Apply a Cat-card triple requesting both present and absent card titles.
3. Apply five-card combinations with a Cat title in every component position.
4. Retrieve a `cat:*` card through a five-card combination.
5. Verify Favor and pair actions exclude every empty-handed opponent.
6. Verify triples may still target an empty-handed opponent and simply fail to obtain the requested title.
7. Nope and then un-Nope a Cat pair or five-card combination.
8. Verify a failed combination parse cannot leave cards partially moved to the discard.
9. Exercise Attack followed separately by Skip, Defuse, elimination, resolved Attack, and cancelled Attack.
10. Verify two-player and three-to-five-player setup Defuse counts independently.

## Material questions for a human

- Is `GameState` strictly trusted engine state, with players limited to `render()` and current-player actions? If not, player-specific observations are needed to enforce hidden hands, deck order, previews, and secret reinsertion positions.
- Should action encoding be treated as opaque internal syntax? Regardless of the answer, every string returned by `legal_actions()` must be accepted safely by `apply_action()`.

score: 0.62
confidence: high
critical_issues: 1
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true