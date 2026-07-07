### 1. Score

- `score: 0.62`
- `confidence: medium`

This oneshot module implements a coherent four-player CATAN skeleton with correct building costs, production multipliers, harbor rates, robber blocking, and special-card VP thresholds. Substantial simplifications—scripted setup, automatic seven-discard, no inter-player trading, deterministic steal and dev-deck order, and nonfunctional progress cards—keep it below “mostly correct” despite a clean API surface.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook pages 2–3: active player may trade with all opponents via offers and counter-offers; opponents cannot trade among themselves. `cat_claude_os.py` `legal_actions()` main phase lists bank trades only.  
   **why it matters:** Removes the primary resource-acquisition mechanism besides production and development cards.  
   **suggested next action:** Add negotiated or atomic player trades, or scope the benchmark explicitly to bank-only CATAN.

2. **severity: major**  
   **evidence:** Rulebook page 4 §4a: on a 7, players with >7 cards discard half (round down) by choice. `_discard_auto()` applies a fixed greedy discard without player input.  
   **why it matters:** Changes game tree and benchmark fairness versus human CATAN.  
   **suggested next action:** Model discard as a dedicated phase with legal discard combinations summing to required count.

3. **severity: major**  
   **evidence:** Fortschritt cards in rulebook (road building, year of plenty). Playing `("play", idx, "road")` or `"year"` in `apply_action()` deletes the card only.  
   **why it matters:** Legal actions exist that violate rulebook card effects.  
   **suggested next action:** Implement effects or disallow those play actions until ready.

4. **severity: minor**  
   **evidence:** Setup uses immutable `SETUP = [(0,0,44), …]` with one legal action per step. Rulebook beginner diagram is fixed layout but players still choose settlement/road positions subject to rules.  
   **why it matters:** Zero setup branching; all rollouts share identical openings.  
   **suggested next action:** Document as deterministic fixture or expand setup action space.

5. **severity: minor**  
   **evidence:** Steal phase picks `take = sorted(vh.items(), key=lambda x: (x[0]))[0][0]`. Rulebook: victim holds cards hidden; active player steals one unspecified card.  
   **why it matters:** Predictable steals bias benchmarks.  
   **suggested next action:** Use chance node or uniform random over victim hand.

6. **severity: minor**  
   **evidence:** Only one development card play is blocked after purchase (`bought_dev_this_turn`), but after playing monopoly the player remains in main and may play another dev card same turn. Rulebook allows one dev card per turn.  
   **why it matters:** Extra dev-card chaining inflates action set beyond rules.  
   **suggested next action:** Track `played_dev_this_turn` flag.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | 8-step `SETUP`, initial resources from marked second settlements | Fixed placements; beginner board hex/chip layout encoded in `HEXES`. |
| player count and turn order | covered correctly | 4 players, clockwise via `pass` | Matches Einsteiger four-player mode. |
| legal actions | partially covered | build, bank trade, dev buy/play, robber, pass | Missing player trade; stub progress cards. |
| state transitions | partially covered | roll→main or roll→robber; knight→robber | Dev cards not playable before roll phase. |
| terminal conditions | partially covered | 10 VP win on acting player build/buy/knight | Opponent VP changes from special cards not re-checked each transition. |
| scoring/returns | partially covered | `_public_vp`, `_total_vp`, winner gets 1.0 return | Hidden VP dev included in win check. |
| rendering/action names | covered correctly | Consistent `setup:place:`, `move:robber:`, `build:` strings | Good BoardBench interchange. |
| chance handling | partially covered | Dice roll as chance node | Dev deck deterministic. |
| hidden information | partially covered | Per-player dev hands; full render | Steal/discard policies leak structure via determinism. |
| simultaneous moves | not relevant | Turn-based | N/A. |
| robber | partially covered | Blocks production on occupied hex; move + steal sequence | Steal victim must have cards; deterministic card taken. |
| trading | partially covered | 4:1, 3:1, 2:1 harbor via `_harbor_rates` | Bank infinite; no player trades. |

### 4. Unsupported assumptions or invented rules

- **Risky:** Greedy auto-discard on seven.
- **Risky:** No Binnenhandel (player trades).
- **Risky:** Road/year development cards are placeholders.
- **Risky:** Lexicographic steal selection.
- **Risky:** Fixed `DEV_DECK` ordering.
- **Risky:** Possible multiple dev-card plays per turn after first resolves.
- **Harmless convention:** Beginner board geometry hard-coded in adjacency tables.
- **Harmless convention:** Desert robber starts on `D` hex index 9.
- **Harmless convention:** Single winner `returns()` vector.

### 5. Missing scenario tests

- Monopoly then second dev same turn: play monopoly, assert no second dev play legal until next turn.
- Largest army tie at 3 knights: two players with 3; prior holder retains if still tied.
- City doubles production: settlement on hex producing on roll 8 upgraded to city; assert 2 resources not 1.
- Bank 4:1 with exactly 4 brick: trade for grain, assert hand counts.
- Robber on desert move forbidden: assert current robber hex excluded from move list.
- Empty steal: no eligible victim on hex; assert `steal:none` only action.
- Build road connectivity: road must touch own network; illegal edge rejected.
- VP win threshold: 9 public VP + buy VP dev card → terminal.

### 6. Open questions for the human

- Is bank-only trading the intended oneshot scope for CATAN benchmarks?
- Should steal and discard be chance/policy nodes rather than deterministic?
- Must Fortschritt card effects be implemented before CATAN enters cross-game comparisons?
- Is the scripted setup fixture the canonical BoardBench opening for CATAN?

### 7. Machine-readable summary

```text
score: 0.62
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
