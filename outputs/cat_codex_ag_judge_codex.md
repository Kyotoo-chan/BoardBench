### 1. Score

score: 0.55  
confidence: high

The implementation captures a playable skeleton of the supplied CATAN rules: turn phases, explicit dice/dev/steal chance nodes, resource production, building costs, robber flow, development-card restrictions, longest road/largest army, hidden hands, and terminal winner-take-all returns. However, it relies on an invented abstract board, omits player-to-player trade and progress-card effects, has incomplete harbor support, and has some important state-flow issues around development cards and terminal timing. These gaps materially affect rule fidelity and benchmark comparability.

### 2. Top findings

- severity: major  
  evidence: code `_abstract_board()` states it is “not the missing official figure” and uses a small stable graph; rulebook setup requires the beginner page-1 board, starting settlements/roads, harbors, tiles, and number chips.  
  why it matters: board topology drives almost every legal move, yield, longest road, harbor trade, and scenario comparison. An invented graph makes the environment only loosely comparable to the provided rulebook setup.  
  suggested next action: replace the abstract board with extracted/hand-authored beginner board data, or clearly mark this as an intentionally reduced Catan-like model.

- severity: major  
  evidence: rulebook allows Binnenhandel with other players; code only implements `trade:maritime:*` and no player trade protocol.  
  why it matters: trading with other players is a central legal action and can change reachable builds and strategy.  
  suggested next action: either add a bounded active-player trade protocol or document player trade as deliberately unsupported and exclude it from judged fidelity.

- severity: major  
  evidence: rulebook says a player may play one development card at any time during their turn; code only permits `play:knight`, not `Fortschritt`, and VP cards are only counted passively.  
  why it matters: progress cards are a whole dev-card class in the rulebook, and buying/drawing them creates cards that can never be legally used.  
  suggested next action: implement concrete progress effects only if available from allowed text, otherwise make them explicit unsupported assumptions and avoid including unusable `Fortschritt` cards in deck-based tests.

- severity: major  
  evidence: `build:dev` moves to `dev_chance`; after chance resolution, code returns to `"build"` even if the purchase was initiated during build. This is okay, but terminal is checked immediately after drawing a VP card via `_maybe_terminal()`. Rulebook says victory occurs on the player’s own turn at 10+, so that part is plausible; however code can also terminal immediately after `play:knight` in `pre_roll` before robber movement is resolved.  
  why it matters: ending mid-action can skip mandatory robber movement from the played knight.  
  suggested next action: defer terminal checks for knight/largest-army until after the required robber move/steal sequence completes.

- severity: major  
  evidence: `information_state()` starts with `self.render(state)`, and `render()` exposes each player’s `hand_count` and `dev_count`, not card identities; own hand is then shown. This mostly hides private identities, but `render()` is a full public debug view and includes total hand/dev counts for all players.  
  why it matters: hand counts are normally public enough for discard threshold, but hidden dev-card counts may be observable physically; this is probably acceptable, yet benchmark expectations should be explicit.  
  suggested next action: document exactly what public information is assumed visible.

- severity: minor  
  evidence: harbors exist on `Crossing.harbor`, but `_abstract_board()` creates every crossing with `harbor=None`.  
  why it matters: 3:1 and 2:1 sea trade are legal rulebook actions but impossible in the default setup.  
  suggested next action: add harbor locations/types once beginner board data is available.

- severity: minor  
  evidence: `_update_longest_road()` only updates based on the actor and does not remove or reassign the owner if their road is split below threshold by another player’s settlement. The brief flags this as an unclear but important risk.  
  why it matters: longest-road VP can remain stale after road interruption.  
  suggested next action: recompute all players’ longest roads after any road or settlement build and apply a documented tie/drop behavior.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `initial_state()` gives 3/4 players, 2 settlements and 2 roads each, starting resources from lettered settlements | Uses invented abstract board instead of the page-1 beginner setup; no real harbors |
| player count and turn order | partially covered | `num_players in (3, 4)`, `current = (current + 1) % num_players` | Oldest player is modeled as player 0, a harmless convention |
| legal actions | partially covered | phase-based `legal_actions()` covers roll, chance, discard, robber, maritime trade, builds, knight | Missing player trade and progress cards; no interleaving trade/build beyond fixed phases |
| state transitions | partially covered | yield, build payment, city upgrade, robber/discard, dev draw, knight effects implemented | Abstract board and missing trade/progress mechanics limit fidelity |
| terminal conditions | partially covered | `_victory_points()` counts buildings, special cards, hidden VP; terminal winner set at 10+ | Can terminal during knight play before mandatory robber resolution |
| scoring/returns | partially covered | terminal returns winner `+1`, others `-1/(N-1)` | Payoff model is a benchmark convention, not in rulebook |
| rendering/action names | partially covered | stable strings like `build:road:e_xD_1`, deterministic render | Board IDs are invented; action names are usable but not rulebook-native |
| chance handling | mostly covered | explicit `dice_chance`, `dev_chance`, `steal_chance`; probabilities provided | Dev deck composition not supplied; default deck empty disables dev buying |
| hidden information | partially covered | `information_state()` shows own hand/dev and hides opponent card identities | Public render includes counts; no per-recipient handling of stolen-card revelation |
| simultaneous/non-sequential phases | partially covered | discard is sequential over `pending_discards` | Rulebook simultaneous discard is modeled as ordered hidden choices, likely acceptable |
| player trade | missing | no `offer`, `accept`, `reject`, or active-player exchange actions | Significant omission |
| harbor trade | partially covered | ratio logic exists | Default board has no harbors, so 3:1/2:1 never occur |

### 4. Unsupported assumptions or invented rules

- Risky: the entire board graph, tile IDs, edge IDs, crossing IDs, number-chip placement, starting settlement locations, and road locations are invented rather than taken from the page-1 beginner setup.
- Risky: no player-to-player trade is implemented, although the rulebook explicitly allows it.
- Risky: progress development cards have no legal action/effect, although the rulebook says their text is executed.
- Risky: development deck composition is caller-supplied and defaults to empty.
- Risky: longest-road ownership never drops or reassigns except when another actor strictly exceeds the current owner.
- Risky: terminal can be triggered immediately after `play:knight`, before the required robber move/steal sequence completes.
- Harmless convention: oldest player is represented as player 0.
- Harmless convention: returns use zero-sum winner-take-all values because the rulebook gives victory conditions, not numeric payoffs.
- Harmless convention: public rendering uses ASCII-like German labels without umlauts, e.g. `Weiss`, `Huegelland`, `Wueste`.
- Unclear: opponent hand counts and dev-card counts are exposed in render/information state; this may be acceptable as physical table information but is not specified in the supplied text.

### 5. Missing scenario tests

- Initial setup: assert 3-player setup removes player 3/red pieces and that each active player has exactly 2 settlements and 2 roads.
- Yield example: from initial state, apply `roll`, then `chance:dice:3`; verify White gets `Holz`, Blue gets `Erz`, Orange gets `Erz` according to the supplied example.
- City yield: upgrade a White settlement adjacent to the 10 Weideland, roll 10, and verify 2 `Wolle`.
- Robber on 7: give one player 9 cards, apply `chance:dice:7`, verify exactly 4 cards must be discarded before robber movement.
- Robber blocking: move robber to a productive tile, roll that tile’s number, verify adjacent settlements/cities receive no resources.
- Development-card freshness: buy `Ritter`, verify it cannot be played before end turn, then can be played on a later turn.
- Knight terminal timing: create a state where playing a third knight gives largest army and 10 VP; verify robber movement is still required or explicitly skipped by design.
- Maritime harbor: once harbor data exists, verify 4:1 always, 3:1 only at a 3:1 harbor, and 2:1 only at the matching special harbor.
- Player trade omission/regression: assert no player-trade action exists and mark expected unsupported behavior, or add tests for an implemented bounded trade protocol.
- Longest-road split: create a player road of length 6/7, build an opponent settlement that interrupts it, and verify ownership/length follows the documented rule decision.

### 6. Open questions for the human

- Should this implementation be scored as a reduced Catan-like environment because the official beginner board graph was unavailable, or should the page-1 figure be manually encoded before judging benchmark readiness?
- Should player-to-player trade be required for this benchmark, or intentionally excluded to keep the action space finite?
- Are progress-card effects available from another allowed source, or should `Fortschritt` cards be removed/disabled until their text is supplied?
- What exact convention should be used when longest road is broken below five or tied, since the supplied text only clearly specifies taking it by becoming strictly longer?

### 7. Machine-readable summary

```text
score: 0.55
confidence: high
critical_issues: 0
major_issues: 5
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```