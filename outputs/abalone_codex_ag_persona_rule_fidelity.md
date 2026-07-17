## Major finding

### Forced pass is missing when no legal movement exists

- **Fact ID:** Unnumbered approved human decision dated 2026-07-17 (forced-pass convention)
- **Evidence type:** `human_decision`
- **Page:** N/A — the canonical facts explicitly identify this as a rulebook source gap.
- **Direct quote:** “if and only if a player has no legal movement, expose one forced pass that advances the turn.”
- **Code location:** [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_rule_fidelity_oyleoxqp/implementation.py:64), particularly lines 68–98; enforcement at lines 101–103.
- **Expected behavior:** A nonterminal state with no legal movement exposes exactly one forced-pass action. Applying it changes the active player without moving marbles.
- **Actual behavior:** `legal_actions()` returns an empty tuple when `_groups()` produces no legal move. No pass action is generated or handled, and `apply_action()` rejects anything outside that empty set. The game therefore cannot advance.
- **Severity:** Major
- **Confidence:** High

No critical findings identified.

## Coverage

Covered rule areas:

- Figure 1 board shape, inventory, setup, and Black moving first
- Selection of one to three contiguous collinear marbles
- Inline and broadside movement
- One-pit movement and empty-destination requirements
- Sumito strength limits, alignment, adjacency, blocking, and edge ejection
- Equal-strength Patt restrictions and the three-marble strength cap
- Sixth-ejection termination and winner returns
- Strict alternation following ordinary applied moves

Uncovered or intentionally outside implementation scope:

- Social/random assignment of people to colors
- Optional clocks and timeout outcomes
- Draw or repetition behavior, which the source does not specify

Qualitatively, the implementation closely follows the canonical board and movement rules. Its concrete fidelity gap is the approved forced-pass convention: a no-move nonterminal position deadlocks instead of advancing the turn.