## Critical/major findings

### 1. No forced-pass transition when a player has no legal movement

- Fact ID: No numbered rule fact; approved interface decision in `canonical_rulefacts.md` lines 83–84
- Evidence type: Approved human decision addressing a printed-source gap
- Page: N/A
- Quote: “if and only if a player has no legal movement, expose one forced pass that advances the turn.”
- Code locations: [implementation.py:64](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_executable_systems_i9cn5n5g/implementation.py:64), [implementation.py:101](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_executable_systems_i9cn5n5g/implementation.py:101)
- Expected behavior: A nonterminal state with no movement must expose exactly one forced-pass action. Applying it must preserve the board and ejection counts and advance `player`.
- Actual behavior: `legal_actions()` returns an empty tuple. There is no pass action representation or application path, leaving such a state nonterminal but unable to transition.
- Severity: Major
- Confidence: High

## Other executable-boundary observations

- Setup invariants: `initial_state()` appears consistent with SET-03 through SET-05: 61-pit radius-four geometry, 14 marbles per color, and the printed row arrangement. Black is player zero, satisfying TURN-01.
- Sumito timing is atomic: defenders move and ejections are recorded within the initiating action. There is no unsupported pending-reaction state.
- Strict superiority, the 2v1/3v1/3v2 limits, obstruction, collinearity, broadside emptiness, and edge ejection are represented directly in `legal_actions()`.
- Terminal transition is immediate for the public turn API: `current_player()` returns `None` once either ejection count reaches six, and further actions are unavailable.
- Minor stale-status issue: [implementation.py:147](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_executable_systems_i9cn5n5g/implementation.py:147) always renders `Am Zug` using the toggled `state.player`, even for terminal states where `current_player()` is `None`. END-01 implies there is no next turn after the sixth ejection.
- State-validation evaluator question: public `GameState` accepts invalid colors, players, coordinates, duplicate cells, negative ejection counts, and inventory-inconsistent positions. The approved facts do not specify whether this low-level constructor must reject malformed fixtures, so this is not classified as a code defect.
- Source gap: the approved forced-pass decision specifies that a pass exists, but not its serialized `Action` shape or display name. The evaluator needs a stable convention.
- Chance and hidden information: color assignment is the only stated random/social setup operation, and player identities are absent from this API. There is no hidden knowledge to become stale.
- Clock, timeout, draw, and repetition transitions are correctly absent from the core implementation under CLOCK-01 and END-02.

## Deterministic regression candidates

1. **Canonical setup:** Assert 28 occupied cells, 14 of each color, 33 empty playable pits, exact SET-05 coordinates, and current player Black.
2. **Forced pass:** Construct a nonterminal state with no legal movement; assert exactly one pass, then assert unchanged board/ejections and toggled player.
3. **Pass exclusion:** For the initial state and every fixture containing a legal movement, assert no pass is exposed.
4. **Strict Sumito table:** Fixture-test 2v1, 3v1, and 3v2 as legal; 1v1, 2v2, 3v3, and effective 4v3 as illegal.
5. **Push obstruction:** Assert illegality with a friendly or opposing marble immediately behind the defenders.
6. **Gap and angle:** Assert that a separated or non-collinear opposing group cannot be pushed.
7. **Broadside occupancy:** Assert all selected destinations must be on-board and empty and that opponents never move broadside.
8. **Sixth ejection:** Begin at five opponent ejections, apply one legal edge Sumito, and assert immediate terminal status, correct returns, no legal actions, and no advertised next player.
9. **Fifth ejection:** Apply the equivalent edge Sumito from four ejections and assert nonterminal status and strict turn alternation.
10. **Terminal rendering:** Assert terminal output reports the winner or completion state and does not contain `Am Zug`.