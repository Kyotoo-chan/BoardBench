score: 0.66, confidence: high. The fixed setup, phase order, production, robber, trading, construction, special-card calculations, and ordinary scoring are substantially implemented. The main weaknesses concern winning transitions and concealed victory-point information: one valid winning action can crash, turn-start victory is omitted, mandated VP revelation is absent, and `render()` leaks hidden VP totals.

## Findings

### Major — Winning with a free Road Building road crashes

- Canonical fact: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`
- Locator: `/Approved human decisions (2026-07-23)/2`
- Exact evidence: “Check victory after every completed atomic action or committed subaction… This includes … the first free road of Road Building.”
- Conflicting transition: `apply_action()` → `place_free_road`; `_place_road()` → `_victory()`.
- Expected: If the first or second free road raises the active player to ten points, that road completes atomically and the game immediately enters a valid terminal state.
- Implemented: `_place_road()` invokes `_victory()`, which sets `pending = None`. Control then returns to `place_free_road`, which executes `d["pending"]["remaining"] -= 1`. This attempts to index `None` and raises instead of returning the winning state.
- Impact: A legal terminal action fails precisely when Road Building establishes victory.

### Major — No victory check when a player becomes active

- Canonical fact: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`
- Locator: `/Approved human decisions (2026-07-23)/2`
- Exact evidence: “Check victory after every completed atomic action or committed subaction… This includes turn start before rolling.”
- Conflicting transition: `apply_action()` → `end_turn`, followed by `legal_actions()` in phase `roll`.
- Expected: After the next player becomes active, immediately terminate if that player already has at least ten points.
- Implemented: `end_turn` changes the active player and enters `roll` without calling `_victory()`. The new active player is offered `roll_dice`.
- Impact: A player who acquired ten points while inactive—for example through a Longest Road reassignment—does not win at the approved time and may be forced to roll.

### Major — Hidden victory-point cards are never revealed to establish victory

- Canonical fact: `CAT-D-VP-REVEAL`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`
- Locator: `/Approved human decisions (2026-07-23)/8`
- Exact evidence: “Victory detection automatically reveals, in development-hand order, only the minimum number of hidden victory-point cards needed to establish ten.”
- Conflicting symbol: `_victory()`, `_score()`, `observation_to_data()`.
- Expected: Victory detection marks the minimum necessary VP cards as revealed, preserves any surplus VP cards as hidden, and exposes the resulting winning public score.
- Implemented: `_victory()` merely sets terminal fields. All VP cards remain in an undifferentiated concealed `development_hand`, while `public_scores` continues to call `_score(..., False)` and can therefore show fewer than ten points for the winner.
- Impact: The terminal state does not represent the approved revelation or publicly substantiate the victory.

### Major — Public rendering exposes concealed VP-card points

- Canonical fact: `CAT-INFO-01`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`
- Locator: PDF p. 4, “Siegpunkte”
- Exact evidence: “Karten mit Siegpunkten werden grundsätzlich geheim gehalten. Sie werden erst aufgedeckt, wenn ein Spieler insgesamt 10 Siegpunkte erreicht hat.”
- Conflicting symbol: `render()` calls `_score(d, player_id)` with its default `include_hidden=True`.
- Expected: Publicly rendered scores exclude concealed victory-point cards until those cards establish victory.
- Implemented: `render()` includes every player’s hidden VP cards in displayed scores. Comparing the rendered score with visible board and special-card points reveals the number of concealed VP cards.
- Impact: Material private development-card information is leaked during play.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Fixed four-player setup and inventories | Covered; constants, starting pieces, hands, bank, deck, and robber agree with approved facts |
| Turn flow | Strict roll → trade → build is represented; turn-start victory is missing |
| Production and seven | Covered, including city yield, robber blocking, private aggregate discard, and mandatory robber movement |
| Domestic/maritime trade | Covered, including active-player-only bilateral legs, positive exchanges, atomic commit, and harbor rates |
| Construction and stock | Covered, including costs, road connectivity, distance rule, city replacement, and returned settlement |
| Development cards | Main effects and one-per-turn timing covered; winning Road Building transition is defective |
| Longest Road/Largest Army | Edge-simple trail and holder/tie rules appear covered |
| Private information | Observation structure mostly complies; `render()` leaks hidden VP totals |
| Scoring and terminal state | Ordinary score calculation works; turn-start checks and VP revelation are incomplete |
| Returns | Terminal winner receives `+1`, all others `-1`; nonterminal returns are zero |

## Missing deterministic scenarios

- Road Building’s first free road raises the active player from eight to ten through Longest Road.
- Road Building’s second free road establishes ten points.
- An inactive player reaches ten after another player’s settlement interrupts and reallocates Longest Road, then becomes active.
- Victory requiring exactly one concealed VP card, with additional VP cards remaining hidden.
- Victory requiring multiple concealed VP cards, verifying development-hand reveal order.
- Public `render()` with one or more concealed VP cards, compared with visible public points.
- A Road Building subphase with no remaining legal road, verifying whether querying legal actions may advance state.

## Material questions for a human

- `legal_actions()` mutates the supplied state when Road Building has no legal placement by calling `_finish_road_building(d)`. The packet does not explicitly state whether legal-action enumeration must be pure. Should this transition instead be represented by an explicit action or performed only while applying an action?
- Should `render()` be treated as a public player-facing view? If it is purely privileged debugging output, the VP disclosure finding’s interface impact would be reduced, though the observation/revelation defect remains.

No publisher-rule clarification is needed for the scored findings; three arise from explicit approved human decisions and one directly contradicts the printed secrecy rule.

score: 0.66
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true