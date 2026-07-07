### 1. Score

- `score: 0.66`
- `confidence: medium`

Agentic CATAN extends the oneshot implementation with deterministic 1:1 player trades, partially addressing the rulebook’s Handel phase. Core mechanics—production, building, robber, knights, monopoly, bank/harbor rates, and VP scoring—remain largely intact. Persistent simplifications (scripted setup, auto-discard, incomplete progress cards, fixed dev deck, infinite bank) cap the score below 0.7 despite the trading improvement.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook describes negotiated trades between active player and each opponent separately. Agentic code adds `ptrade` actions: instant 1:1 exchange if partner holds the requested card—no proposal/acceptance, no multi-card ratios.  
   **why it matters:** Better than oneshot but still a coarse abstraction of Binnenhandel.  
   **suggested next action:** Clarify benchmark trade model; optionally add accept/decline or ratio parameters.

2. **severity: major**  
   **evidence:** Seven rolled → `_discard_auto()` for all players with >7 cards. Rulebook: player selects cards to discard, half rounded down.  
   **why it matters:** Identical gap in both variants; affects steal targets after ptrade-enriched hands.  
   **suggested next action:** Player discard phase or fixed policy documentation.

3. **severity: major**  
   **evidence:** `"road"` and `"year"` dev-card plays remove card without granting roads/resources.  
   **why it matters:** Dev-card action space includes invalid outcomes.  
   **suggested next action:** Implement or remove stub actions.

4. **severity: minor**  
   **evidence:** ptrade enumerates all partner/give/take combinations where partner has `take` and active player has `give`; can produce large action lists.  
   **why it matters:** Branching factor may dominate rollouts; differs from sparse human negotiation.  
   **suggested next action:** Consider action filtering or trade proposal cap for benchmarks.

5. **severity: minor**  
   **evidence:** Rulebook: opponents may not trade with each other—only with active player. ptrade correctly restricts to `partner != p` during active turn.  
   **why it matters:** Positive fidelity detail in agentic variant.  
   **suggested next action:** Preserve in future trade models.

6. **severity: minor**  
   **evidence:** Steal uses lexicographic first resource; dev deck fixed order; bank infinite.  
   **why it matters:** Shared deterministic shortcuts.  
   **suggested next action:** Shared fixes across os/ag.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Shared `SETUP` sequence | No choice placements. |
| player count and turn order | covered correctly | 4-player rotation | Same as oneshot. |
| legal actions | partially covered | + ptrade vs oneshot | Trading partially covered; dev stubs remain. |
| state transitions | partially covered | ptrade in main only | No trade during robber/setup. |
| terminal conditions | partially covered | 10 VP threshold | Acting-player win checks only. |
| scoring/returns | partially covered | Building and special VP | Unchanged from oneshot. |
| rendering/action names | covered correctly | `trade:p{n}:1:res->res` | Parses via `name_to_action`. |
| chance handling | partially covered | Roll chance node | No shuffle/steal chance. |
| hidden information | partially covered | ptrade requires knowing partner resources | Full render exposes all; realistic for benchmark. |
| simultaneous moves | not relevant | Turn-based | N/A. |
| Binnenhandel | partially covered | Atomic ptrade | No negotiation loop. |
| Seehandel | covered correctly | Bank and harbor trades | Same as oneshot. |

### 4. Unsupported assumptions or invented rules

- **Risky:** Forced 1:1 ptrade without partner consent.
- **Risky:** Auto-discard policy on 7.
- **Risky:** Nonfunctional road/year dev cards.
- **Risky:** Deterministic steal; fixed dev deck; infinite bank.
- **Harmless convention:** ptrade only in main phase after production/robber.
- **Harmless convention:** Trade action naming distinct from bank prefix.

### 5. Missing scenario tests

- ptrade changes both hands: p0 trades brick for grain with p2; verify counts on both sides.
- No ptrade when partner empty of take resource.
- ptrade then build: trade for missing settle resource, build settlement same turn.
- Agentic-only: state with trade opportunity; oneshot has no ptrade, agentic does.
- Multiple ptrade partners: actions exist for each eligible partner independently.
- ptrade string align: cross-variant action language test with oneshot (bank only) and agentic (bank+trade).
- Steal after ptrade: victim’s hand changed by trade affects steal outcome.
- One dev per turn: play knight, resolve robber, assert no second dev play same turn (if enforced).

### 6. Open questions for the human

- Is forced 1:1 ptrade an acceptable stand-in for CATAN negotiation in agentic benchmarks?
- Should agentic and oneshot share the same score weight for trading in cross-variant charts?
- When will Fortschritt card effects be implemented for both variants?
- Should ptrade action explosion be capped for rollout budgets?

### 7. Machine-readable summary

```text
score: 0.66
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
