### 1. Score

- `score: 0.68`
- `confidence: medium`

The agentic variant preserves the oneshot CATAN core and adds simplified 1:1 player trades (`ptrade`), improving coverage of the rulebook trading phase relative to bank-only exchange. Remaining gaps—scripted setup, auto-discard on 7, stubbed Fortschritt cards, fixed dev deck, infinite bank, and deterministic steal—keep the score in the “playable but simplified” band rather than benchmark-complete.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook p.3 Binnenhandel: active player negotiates multi-card offers and counter-offers; opponents cannot trade with each other. Code adds atomic `("ptrade", partner, give, take)` 1:1 swaps when partner holds the requested resource—no multi-resource deals, no offer/counter structure, partner cannot refuse.  
   **why it matters:** Captures player-to-player exchange in simplified form but omits negotiation depth and consent mechanics central to CATAN trading.  
   **suggested next action:** Document as atomic trade benchmark model or extend to multi-ratio offers with accept/decline.

2. **severity: major**  
   **evidence:** Roll-7 discard per rulebook requires player choice of half (rounded down). `_discard_auto()` still applies in both variants.  
   **why it matters:** Unchanged from oneshot; affects post-trade and post-build states.  
   **suggested next action:** Expose discard choices or keep documented auto-policy.

3. **severity: major**  
   **evidence:** Fortschritt cards (road, year) play actions exist but perform no effect beyond removing the card (`apply_action` play branch for `"road"`/`"year"`).  
   **why it matters:** Incomplete dev-card semantics remain a fidelity gap.  
   **suggested next action:** Implement road-building and year-of-plenty sub-phases.

4. **severity: minor**  
   **evidence:** Agentic `ptrade` allows any 1:1 swap if partner has the take resource; rulebook trades are voluntary and may involve unequal ratios (e.g., 2:1 offers).  
   **why it matters:** Action space is larger and more permissive than typical negotiated trades but still closer than no player trades.  
   **suggested next action:** Accept as simplified superset or constrain to common ratios.

5. **severity: minor**  
   **evidence:** Fixed `SETUP`, `DEV_DECK`, infinite bank, deterministic steal—same as oneshot.  
   **why it matters:** Shared simplifications limit both variants equally.  
   **suggested next action:** Address in shared baseline or document conventions.

6. **severity: minor**  
   **evidence:** `trade:p{partner}:1:{give}->{take}` naming added in `action_to_name`; round-trip via `name_to_action` works.  
   **why it matters:** Positive for BoardBench action-language alignment between variants.  
   **suggested next action:** Add pair-align tests for ptrade strings.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Same scripted `SETUP` as oneshot | Fixed beginner fixture. |
| player count and turn order | covered correctly | 4 players, clockwise rotation | Unchanged. |
| legal actions | partially covered | Bank, ptrade 1:1, build, dev, robber | Trading improved vs oneshot; still not full negotiation. |
| state transitions | partially covered | ptrade updates hands in main phase | Same phase model otherwise. |
| terminal conditions | partially covered | 10 VP win check on select actions | Same as oneshot. |
| scoring/returns | partially covered | VP and special cards | Unchanged. |
| rendering/action names | covered correctly | Adds `trade:p*` prefix for ptrade | Good extension over oneshot. |
| chance handling | partially covered | Dice chance only | Fixed dev deck. |
| hidden information | partially covered | Partner hand visible to logic for ptrade legality | Full render still shows all hands. |
| simultaneous moves | not relevant | Sequential | N/A. |
| player trading | partially covered | `ptrade` in `legal_actions` lines 387–397 | Atomic 1:1 only; no refusal phase. |
| bank/harbor trade | covered correctly | Same as oneshot | Infinite bank assumption. |

### 4. Unsupported assumptions or invented rules

- **Risky:** Atomic forced 1:1 ptrade (partner cannot decline; only 1:1 ratios).
- **Risky:** Auto-discard on seven.
- **Risky:** Stub road/year development cards.
- **Risky:** Deterministic steal and fixed dev deck order.
- **Risky:** Infinite bank supply.
- **Harmless convention:** ptrade only during active player main phase (matches “only active player trades with others”).
- **Harmless convention:** Same beginner board encoding as oneshot.

### 5. Missing scenario tests

- ptrade legality: p0 has brick, p1 has grain; assert `trade:p1:1:brick->grain` legal and updates both hands 1:1.
- ptrade blocked: partner lacks take resource; assert action not generated.
- ptrade + bank same turn: execute ptrade then harbor 2:1; assert both succeed in main phase.
- Compare vs oneshot: identical state after setup; oneshot lacks ptrade actions, agentic includes them.
- ptrade does not bypass harbor: 2:1 wool harbor still requires 2 wool for 1 other resource.
- Monopoly after ptrade: resources gained via ptrade can be stolen by monopoly same turn.
- Self-trade impossible: no ptrade with `partner == p`.
- Action round-trip: `name_to_action(action_to_name(ptrade))` identity.

### 6. Open questions for the human

- Is atomic 1:1 ptrade the intended agentic approximation of Binnenhandel?
- Should partners be able to reject trades, or is forced swap acceptable for benchmarking?
- Should multi-card trades (2:1, 3:1 between players) be in scope?
- Are remaining oneshot gaps (auto-discard, dev stubs) shared blockers for both variants?

### 7. Machine-readable summary

```text
score: 0.68
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
