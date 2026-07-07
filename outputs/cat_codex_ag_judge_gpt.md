### 1. Score

score: 0.45  
confidence: medium

The implementation captures several core CATAN mechanics: 3–4 players, dice chance, resource production, basic building costs, robber/discard flow, knight/largest-army handling, and terminal winner-take-all returns. However, it uses an invented abstract board, omits player-to-player trading, has no usable default development deck, does not implement progress cards, and effectively omits harbors/special maritime trade, all of which materially affect gameplay and benchmark fidelity.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook explicitly includes Binnenhandel: “Der Spieler kann mit allen Spielern Rohstoffkarten tauschen”; code `legal_actions()` only generates `_maritime_trade_actions()` and no player-trade actions.  
   **why it matters:** Player trading is a central CATAN mechanic and strongly affects resource availability and strategy.  
   **suggested next action:** Add a bounded deterministic player-trade protocol or explicitly mark player trading unsupported in the environment scope.

2. **severity: major**  
   **evidence:** Code `_abstract_board()` states it is “not the missing official figure” and invents a small graph while the rulebook setup depends on the page-1 beginner board.  
   **why it matters:** Board topology, starting positions, tile adjacency, harbors, and number chips determine legal builds and yields. Benchmark comparisons will be unreliable.  
   **suggested next action:** Encode the actual beginner board from the supplied figure, or make board data an explicit required input.

3. **severity: major**  
   **evidence:** Rulebook includes 3:1 and 2:1 harbor trades; code has harbor fields but `_abstract_board()` sets every `Crossing(..., harbor=None)`.  
   **why it matters:** Legal maritime trades are incomplete; special harbor strategy is absent.  
   **suggested next action:** Add harbor locations and resource-specific harbor labels from the rulebook figure or mark them unavailable.

4. **severity: major**  
   **evidence:** Rulebook has development cards `Ritter`, `Fortschritt`, `Siegpunkte`; code default `dev_deck` is empty and `_playable_dev_actions()` only supports `play:knight`.  
   **why it matters:** Development-card purchases are unavailable by default, and progress cards cannot be played even if present.  
   **suggested next action:** Provide a rulebook-supported dev deck composition if available; otherwise require caller-supplied composition and add explicit unsupported handling for `Fortschritt`.

5. **severity: major**  
   **evidence:** Longest road ownership is updated only around the acting player in `_update_longest_road()`. The rulebook example notes that a foreign settlement can split another player’s road.  
   **why it matters:** Special-card VP ownership can become stale after a settlement breaks another player’s road.  
   **suggested next action:** Recompute all players’ longest road lengths after road or settlement builds and handle loss/tie behavior according to clarified rules.

6. **severity: minor**  
   **evidence:** Code uses p0 as oldest/current starter. Rulebook says “Es beginnt der älteste Spieler” but does not map this to a color/player index.  
   **why it matters:** Mostly harmless, but deterministic tests should know the convention.  
   **suggested next action:** Document p0 as the oldest-player convention.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Starts 3–4 players with 2 settlements/2 roads and starting resources from lettered settlements | Board graph, harbors, and exact beginner layout are invented/unclear |
| player count and turn order | partially covered | Supports 3 or 4 players; current advances clockwise by index | Oldest player mapped to p0 by assumption |
| legal actions | partially covered | Roll, discard, robber, basic build, 4:1 maritime trade, knight play | Missing player trades, progress-card play, harbor trades in practice |
| state transitions | partially covered | Dice yield, robber movement/steal, discard, build payments mostly implemented | Abstract board affects connectivity; longest-road reassignment incomplete |
| terminal conditions | mostly covered | Active player wins at ≥10 VP; hidden VP cards counted | Possible early terminal during knight before robber resolution is questionable |
| scoring/returns | partially covered | Terminal winner +1, others negative | Payoff convention is invented; rulebook only specifies winner |
| rendering/action names | mostly covered | Stable string action names and deterministic render | Board IDs are invented; `pass` has phase-dependent meaning |
| chance handling | mostly covered | Explicit dice/dev/steal chance nodes | Dev chance only works if caller supplies deck |
| hidden information | partially covered | Hands/dev identities hidden in `information_state`, own info shown | Counts are visible; probably acceptable but not fully specified |
| simultaneous moves | unclear/partially covered | Discard after 7 handled sequentially | Rulebook does not specify simultaneous protocol |

### 4. Unsupported assumptions or invented rules

- **Risky:** Invented abstract board topology, tile adjacency, starting positions, number chips, and roads.
- **Risky:** No player-to-player trade protocol despite explicit rulebook trading.
- **Risky:** All harbors absent, so 3:1 and 2:1 trades are effectively unavailable.
- **Risky:** Empty default development deck; development cards only work if externally supplied.
- **Risky:** `Fortschritt` cards have no legal play action/effect.
- **Risky:** Longest-road ownership retention/loss behavior is chosen incompletely.
- **Risky:** Winner-take-all numeric returns are invented because rulebook gives only win condition.
- **Harmless/conventional:** p0 represents the oldest starting player.
- **Harmless/conventional:** Resource bank is unlimited; card depletion is not specified in the text.
- **Harmless/conventional:** Discards after rolling 7 are resolved sequentially.
- **Harmless/conventional:** Robber steal chance is represented by resource type probabilities rather than physical card identity.

### 5. Missing scenario tests

- Initial setup: verify 3-player game has no red pieces and each player has 2 settlements/2 roads.
- Initial resources: verify Blue gets `Holz+Erz+Lehm` and Orange gets `Erz+2Getreide` from the lettered settlements.
- Dice yield: `roll`, `chance:dice:3` should give White `Holz`, Blue `Erz`, Orange `Erz` according to the rulebook example.
- Robber/discard: set a player to 9 cards, then `roll`, `chance:dice:7`, require exactly `discard:<4 cards>`.
- Robber steal: after moving robber to a tile adjacent to an opponent with cards, test `robber:steal:pX`, `chance:steal:<resource>`.
- Maritime trade: with 4 identical cards, test `trade:maritime:4:Holz->Erz`.
- Harbor trade: add/verify a 3:1 and 2:1 harbor settlement and test those legal actions.
- Player trade: active player offers resources to another player and receives acceptance/rejection.
- Development card: buy `Ritter`, confirm it cannot be played same turn, then can be played next own turn.
- Progress card: buy and play `Fortschritt`, or verify unsupported behavior is explicit.
- Longest road: build 5-road chain, assign `Längste Handelsstraße`; then split it with a foreign settlement and recompute ownership.
- Terminal: active player reaches 10 VP from city/build/dev VP and receives terminal return.

### 6. Open questions for the human

- Is an invented abstract board acceptable, or must the implementation encode the exact beginner board from the page-1 figure?
- Should player-to-player trading be fully modeled, bounded/abstracted, or intentionally excluded?
- What development-card composition and `Fortschritt` card effects should be used?
- What is the desired return convention: winner `1`/others `0`, zero-sum, or VP-based?
- How should longest-road ownership behave when the current holder’s road is split below 5 or tied?

### 7. Machine-readable summary

```text
score: 0.45
confidence: medium
critical_issues: 0
major_issues: 5
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
