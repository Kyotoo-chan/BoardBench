Scope was limited to `SOURCE_MANIFEST.md`, `RULES_publisher_rulebook.pdf`, `COMPONENTS_user_observation.pdf`, `approved_rulefacts.md`, supplied page images, and `implementation.py`. `RULES` governs gameplay; `COMPONENTS` was used only for approved inventory/yield observations.

## Material code defects

### 1. Inactive players cannot exercise the anytime-harvest right

- Fact ID: `HARV-01`
- Evidence type: `RULES`, publisher rulebook; approved human timing decision
- Page: RULES p.7
- Quote: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Code: [implementation.py:104](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:104), especially lines 107–149 and validation at [implementation.py:202](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:202)
- Expected behavior: Between atomic steps, every player must have an opportunity to harvest an eligible own field, including during another player’s turn.
- Actual behavior: Harvest actions are generated only for `state.decision`. There is no interrupt/reaction mechanism by which another owner can become the decision player. During ordinary phase 1/2/4 actions, that means only the active player can harvest; while awaiting trade consent, only the partner can.
- Severity: Major
- Confidence: High

This also affects multi-step phase-3 planting: owners not currently selected cannot harvest between another owner’s individual plant actions.

### 2. A trade recipient must accept or reject without observing the proposal

- Fact IDs: `TRADE-05`, supported by `TRADE-04`, `TRADE-06`, `TRADE-07`
- Evidence type: `RULES`, publisher rulebook, clear
- Page: RULES p.6
- Quote: “Denn beide Spieler müssen dem Handel zustimmen.”
- Code: Trade parameters are held at [implementation.py:28](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:28); consent actions at lines 123–135; proposal switches control at lines 226–227; observation at [implementation.py:272](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:272)
- Expected behavior: Before explicitly accepting or rejecting, the partner must observe the proposal’s parties and actual offered/requested cards or otherwise unambiguous transfer parameters.
- Actual behavior: `render()` exposes no `trade` data. Once `awaiting_consent` is true, the partner receives only `("Handel annehmen",)` and `("Handel ablehnen",)`. Neither selected card identities nor even the selected index sets are observable. This is especially defective for cards offered from the active player’s hidden hand, but also prevents distinguishing which public revealed cards are included.
- Severity: Major
- Confidence: High

The approved hidden-information convention does not justify this omission: it hides an opponent’s general hand, not the contents of a concrete proposal requiring consent.

### 3. Mandatory phase-3 cards disappear from the observation before planting

- Fact IDs: `P3-01`, `P3-02`
- Evidence type: `RULES`, publisher rulebook, clear
- Page: RULES p.7
- Quotes:
  - “Alle Spieler, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen.”
  - “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Code: Queue construction and clearing of visible zones at [implementation.py:240](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:240); planting actions at lines 136–147; observation at [implementation.py:272](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:272)
- Expected behavior: Each recipient observes all cards they must plant and explicitly chooses their planting order and destinations.
- Actual behavior: On ending trade, cards move into `plant_queue`, while `sideways` and `revealed` are cleared. `render()` exposes neither `plant_queue` nor an equivalent owner-specific pending-card view. The player receives index-based `Querkarte anbauen` actions without being shown which bean each queue index represents.
- Severity: Major
- Confidence: High

Compatible field choices may sometimes permit inference, but that is not a reliable or explicit representation of the pending cards.

### 4. Shuffle chance state is outside `GameState`, making branch replay stateful

- Fact ID: `DECK-01`
- Evidence type: `RULES` plus approved human continuation decision
- Page: RULES p.9
- Quote: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
- Code: RNG retained on the `Game` object at [implementation.py:64](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:64); shuffle at [implementation.py:152](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:152); only `GameState` is copied at [implementation.py:202](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_executable_systems_sybxyrde/implementation.py:202)
- Expected behavior: A saved state must either contain its chance state, produce an explicit chance transition, or otherwise replay predictably under the documented seed.
- Actual behavior: Applying a reshuffling action advances `self._rng`, but that RNG state is not copied with `GameState`. Reapplying the same action to the same state on the same `Game` can therefore yield a different shuffled deck. Exploring one branch changes later results of another branch.
- Severity: Major under ordinary finite-state/search/replay semantics
- Confidence: Medium-high

If the evaluator intentionally treats each `Game` instance as a single, non-branching trajectory, this becomes an evaluator-contract question rather than a gameplay defect.

## Source gap and evaluator question

- Empty-draw-pile states: `DECK-01` expressly leaves impossible evaluator-constructed states with insufficient draw and discard cards unresolved. `_draw_one()` returns `None` immediately when `deck` is already empty at lines 152–154, even if discard later contains cards. This should not be scored without a defined convention for that state.
- Start-player configuration: `SET-03`, RULES p.2, says “Bestimmt einen Startspieler.” The implementation fixes player 0 as starter and tie-break origin at lines 46–48 and 197–198. This is valid if player indices are canonically rotated so the chosen starter is always player 0. If external player identities must remain fixed, a start-player parameter is missing.
- No elimination discrepancy was found: `END-06` and the implementation both retain every player through final scoring.
- The 4–5-player setup, 129-card inventory, five-card ordered deal, two initial fields, four-phase obligation, and third-depletion terminal paths are represented consistently with the approved facts.

## Deterministic regression candidates

1. **Inactive harvest interrupt**
   - Active/decision player 0 is in phase 1.
   - Player 1 owns an eligible four-card Blue field.
   - Assert that player 1 can become the decision owner and harvest before player 0’s next atomic action.

2. **Trade-consent payload**
   - Player 0 proposes one known hand card for one card from player 1.
   - Set `decision=1` and `awaiting_consent=True`.
   - Parse `render()` and assert that it identifies both parties and both concrete transfer payloads before accept/reject.

3. **Phase-3 planting observation**
   - Give player 1 pending Soy and Fire cards in `plant_queue`.
   - Clear `sideways` and `revealed`, matching the real transition.
   - Assert that player 1’s observation names both pending cards and that either can be selected first.

4. **Branch-stable reshuffle**
   - Use a fixed seed, one-card deck, first/second depletion count, and a discard pile containing several distinct cards.
   - Apply the same draw action twice from the same saved state on the same game object.
   - Assert identical successor state, or require an explicit chance outcome rather than implicit shared RNG mutation.

5. **Phase-3 inter-owner harvest timing**
   - Queue mandatory cards for players 1 and 2.
   - After player 1 plants one card, give player 2 an eligible harvest.
   - Assert player 2 may harvest before the next individual mandatory planting.

6. **Conditional start-player identity**
   - If player identities are not canonically rotated, configure player 2 as starter.
   - Assert initial active/decision player is 2 and a tied winner is selected by greatest clockwise distance from player 2.
