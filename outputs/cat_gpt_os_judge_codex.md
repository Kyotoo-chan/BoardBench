### 1. Score

score: 0.48  
confidence: high

The implementation is playable as a simplified Catan-like environment and covers several central mechanisms: dice chance, resource production, building costs, robber/discard flow, development-card purchase, hidden hands, and terminal winner returns. However, it replaces the real beginner board with an invented abstract graph, omits player trading, omits progress-card effects, omits harbors except 4:1 trade, assumes a tiny development deck, and implements only a narrow subset of the supplied Catan rule space. These are major benchmark-fidelity gaps.

### 2. Top Findings

1. severity: major  
evidence: Code states the “official beginner board figure is not present” and uses “a small explicit abstract graph”; `TILE_DATA`, `CROSSINGS`, and `EDGE_LABELS` are invented.  
why it matters: Board topology drives almost all Catan legality, resource production, road connectivity, settlement placement, robber targets, and longest-road scoring. An invented graph makes comparisons against the rulebook or later references weak.  
suggested next action: Treat this as an explicit abstraction, or add a rulebook-derived board graph from the page-1 figure.

2. severity: major  
evidence: Rulebook allows Binnenhandel with all players; code says “Player-to-player trading is omitted” and only implements `_maritime_trade_actions`.  
why it matters: Trading is a core legal action and affects resource access, build timing, and strategy. Omitting it materially changes gameplay.  
suggested next action: Add a bounded active-player trade protocol, or document this variant as “bank-trade-only Catan”.

3. severity: major  
evidence: Rulebook defines 3:1 harbors and special 2:1 harbors; code has `HARBORS = {}` and only enables 4:1 unless manually extended.  
why it matters: Harbor ownership is a major consequence of settlement placement and changes legal trade actions.  
suggested next action: Add harbor positions/types if the figure is available; otherwise keep as documented unsupported rulebook data.

4. severity: major  
evidence: Rulebook names `Ritter`, `Fortschritt`, and `Siegpunkte`; code has `DEFAULT_DEV_DECK_COUNTS = (1, 1, 1)` and no legal progress-card play action.  
why it matters: Development cards are under-modeled: deck composition, progress effects, and victory-point card behavior affect scoring and legal actions.  
suggested next action: Add configurable deck composition and either implement progress text from provided material or explicitly exclude progress cards from the deck.

5. severity: minor  
evidence: `render()` exposes all players’ resource hands and dev cards, while `information_state()` hides opponents’ private data.  
why it matters: The debug render is useful for comparison but leaks hidden information if used as a player observation.  
suggested next action: Keep `render()` documented as full debug state and use `information_state()` for player-visible views.

6. severity: minor  
evidence: `is_terminal()` only detects victory during `pre_roll`, `trade`, or `build`; `_maybe_finish()` is called after many actions but not after `end_turn`.  
why it matters: This mostly matches “must be on own turn,” but terminal timing around a player already having 10 VP at start of turn is a modeling choice.  
suggested next action: Add deterministic tests for hidden VP cards and start-of-turn victory detection.

### 3. Rule Coverage Review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Initial settlements/roads and starting resources exist, but board graph and figure data are invented | Preserves some examples but not full beginner setup |
| player count and turn order | mostly covered | Supports 3 or 4 players, red omitted in 3-player by slicing labels; clockwise turn advance | Oldest player modeled as configurable `start_player` |
| legal actions | partially covered | Roll, discard, robber, 4:1 trade, build, buy dev, play knight | Missing player trade, progress cards, harbor trades by default |
| state transitions | partially covered | Resource yields, builds, robber, discard, dev draw, longest road, largest army implemented | Fidelity limited by invented board and incomplete card/trade rules |
| terminal conditions | mostly covered | Active player with >=10 VP wins; hidden VP dev cards count | Needs focused tests for timing and hidden VP reveal behavior |
| scoring/returns | partially covered | VP tracked; terminal winner gets +1, others split negative | Returns are a modeling choice not specified in rulebook |
| rendering/action names | mostly covered | Stable string actions and deterministic render | Render leaks hidden state; acceptable only as debug |
| chance handling | mostly covered | Explicit dice, dev draw, robber steal chance nodes | Dev deck composition assumed; robber steal by resource type, not individual card |
| hidden information | partially covered | `information_state()` hides opponent hands/dev cards | `render()` reveals all private data |
| simultaneous/non-sequential phases | partially covered | Discard is sequential over pending players | Rulebook says all affected players discard; sequence is an implementation assumption |
| player trading | missing | No Binnenhandel protocol | Core rule omitted |
| harbors | partially covered/missing | Code has support structure but no harbors configured | Only 4:1 bank trade works |
| progress cards | missing | No legal `play:progress` actions | Rulebook defers exact text, so full implementation needs Almanach/card text |

### 4. Unsupported Assumptions Or Invented Rules

- Risky: Invented abstract board graph, crossings, edges, tile labels, and tile adjacency.
- Risky: Starting position `A` assigned to Red by assumption.
- Risky: Development deck defaults to one `Ritter`, one `Fortschritt`, one `Siegpunkte`.
- Risky: Progress cards exist in the deck but have no legal effect or play action.
- Risky: Player-to-player trading is omitted entirely.
- Risky: No harbors are enabled because positions/types are not supplied.
- Risky: Resource bank is unlimited.
- Risky: Longest-road drop/tie behavior lets current holder keep the card unless another player is strictly longer.
- Harmless/conventional: `start_player` configurable instead of modeling oldest player.
- Harmless/conventional: Winner-take-all numeric returns.
- Harmless/conventional: Sequential discard resolution after rolling 7.

### 5. Missing Scenario Tests

- Initial state: verify 3-player setup excludes Red pieces and 4-player setup includes all four colors.
- Resource examples: `roll`, `chance:dice:3`; check White gets 1 Holz and Blue/Orange get 1 Erz.
- Resource examples: `roll`, `chance:dice:8`; check Red gets 2 Erz and White gets 1 Erz.
- Robber block: move robber to a producing tile, roll that number, verify no adjacent yield from that tile.
- Discard: give a player 9 cards, roll 7, verify legal `discard:*` actions require exactly 4 cards.
- Robber steal: after robber move to a tile adjacent to an opponent with cards, verify victim selection and `chance:steal:<resource>` probabilities.
- Building legality: insufficient resources, occupied edge, settlement distance rule, and settlement requiring own road.
- Development card freshness: buy `Ritter`, verify it cannot be played until after `end_turn`.
- Largest army: play three old knights and verify 2 VP award, then another player exceeds it and takes the card.
- Longest road: build a 5-road chain, verify award; add a foreign settlement that splits a road and verify current implemented behavior.
- Terminal: player reaches 10 VP during own build phase; verify no legal actions and terminal returns.

### 6. Open Questions For The Human

- Should this benchmark accept an abstract board when the page-1 figure is unavailable as structured data, or should Catan be withheld until the real beginner board graph is encoded?
- Should player trading be omitted for the first benchmark pass, or modeled with a bounded offer/accept action protocol?
- Should progress cards be removed from the generated deck until their exact card text is available?
- Should `render()` be allowed to expose full hidden state as debug output, with `information_state()` used for player-visible state?

### 7. Machine-Readable Summary

```text
score: 0.48
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```