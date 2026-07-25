## Critical/major findings

### EXE-01 — Serialized states do not enforce the 60-card inventory

- **Classification:** Code defect
- **Fact IDs:** WIZ-INV-01, WIZ-INV-03, WIZ-DEC-INV
- **Evidence type:** `clear` rulebook facts plus `human_decision`
- **Page:** 1
- **Quote:** “Inhalt: 60 Charakterkarten …” and “Die vier Magierkarten … Die vier Narrenkarten …”
- **Code location:** [`implementation.py:226`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:226), especially [`implementation.py:239`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:239)–247
- **Expected behavior:** An imported state must contain exactly one rank 1–13 in each of four suits, four Wizards, and four Jesters across all hands and zones—60 cards total, with no missing or duplicated ordinary cards.
- **Actual behavior:** Validation checks each card’s syntax independently but never validates the global multiset or total. States with five Wizards, duplicated ordinary cards, missing cards, or an empty/short deck are accepted. Such states can change trump probabilities, create impossible hands, or later fail at `deck.pop()` during dealing.
- **Severity:** Major
- **Confidence:** High

### EXE-02 — Imported pending trump choices are not tied to the revealed Wizard or dealer

- **Classification:** Code defect
- **Fact IDs:** WIZ-TRUMP-02, WIZ-DEC-TRUMP
- **Evidence type:** `clear` rulebook fact plus `human_decision`
- **Page:** 1
- **Quote:** “Ist die aufgedeckte Karte ein Zauberer, dann darf der Lehrling, der die Karten ausgeteilt hat, eine Trumpffarbe bestimmen, aber erst, nachdem er sich seine Karten angeschaut hat.”
- **Code location:** Normal creation is correct at [`implementation.py:103`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:103)–114; imported-state validation is incomplete at [`implementation.py:236`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:236)–249; trusted by [`implementation.py:119`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:119)–124.
- **Expected behavior:** `choose_trump` must be pending exactly when a Wizard was revealed from a nonempty stack. The dealer must be both `current_player` and `pending.player`; no prediction or card play may occur until one of the four suits is chosen.
- **Actual behavior:** The validator checks only the shape of `pending`. It accepts, for example, `phase="choose_trump"` after a revealed Jester, an arbitrary current player choosing instead of the dealer, or a revealed Wizard with no pending choice. `legal_actions()` then follows the counterfeit phase.
- **Severity:** Major
- **Confidence:** High

### EXE-03 — Round and terminal invariants can be forged at state import

- **Classification:** Code defect
- **Fact IDs:** WIZ-DEAL-01, WIZ-END-01, WIZ-END-02, WIZ-TRUMP-03
- **Evidence type:** `clear`
- **Pages:** 1–2
- **Quote:** “In der ersten Runde wird nur eine Karte … in der zweiten … zwei Karten …” and “Bei 6 Teilnehmern ist das die 10. Stichrunde, bei 5 Teilnehmern die 12., bei 4 Teilnehmern die 15. und bei 3 Teilnehmern die 20. Stichrunde.”
- **Code location:** Correct initial calculation at [`implementation.py:78`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:78)–89 and normal terminal transition at [`implementation.py:174`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:174)–191; missing import constraints at [`implementation.py:233`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:233)–251.
- **Expected behavior:** `max_round` must equal `60 // players`; `round_number` must be within `1..max_round`; terminal state must occur only after the final round has been fully played and scored. Round hand sizes and final-round absence of a reserve/trump card must agree with those values.
- **Actual behavior:** Only integer types are checked. Negative/zero rounds, forged `max_round`, and `terminal=True` during round 1 with `phase="predict"` are accepted. A forged low `max_round` can also make `_finish_round()` terminate early.
- **Severity:** Major
- **Confidence:** High

### EXE-04 — Imported states do not preserve turn, prediction, or partial-trick obligations

- **Classification:** Code defect
- **Fact IDs:** WIZ-BID-01, WIZ-BID-02, WIZ-DEC-BID, WIZ-PLAY-01, WIZ-PLAY-02, WIZ-PLAY-03
- **Evidence type:** `clear` facts plus `human_decision`
- **Page:** 1
- **Quote:** “Es beginnt der linke Nachbar des Kartengebers” and “Die anderen Lehrlinge folgen im Uhrzeigersinn.”
- **Code location:** Turn execution at [`implementation.py:119`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:119)–172; incomplete checks at [`implementation.py:236`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:236)–247.
- **Expected behavior:** Dealer, leader, current player, trick participants, bid completion, and phase must describe one reachable clockwise sequence. Predictions must be `0..round_number`; play cannot start with missing predictions; player indices must be in range; a partial trick cannot contain duplicate or out-of-order actors.
- **Actual behavior:** The validator accepts unrestricted integer indices and predictions, including negative bids, out-of-range current players or trick owners, `play` with `prediction=None`, and duplicate trick participants. Subsequent calls can crash through invalid indexing/scoring or resolve a trick that could not legally occur.
- **Severity:** Major
- **Confidence:** High

## Source gaps and evaluator questions

- **Completed-trick knowledge:** [`observation_to_data()`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:253) exposes the current trick but reduces completed tricks to a count. WIZ-DEC-PRIVACY establishes that hands are private, but the rulebook does not explicitly say whether captured tricks remain inspectable. If observations must provide perfect recall of public play, completed cards and winners are missing; otherwise this is not established as a defect.

- **Portable chance state:** Serialized data includes configuration/chance seeds, but [`_shuffle()`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_executable_systems_i71ur_gy/implementation.py:70) uses the receiving `Game` object’s `self.seed`. Loading the same state into differently constructed `Game` instances can therefore produce different later shuffles. The canonical rules require reshuffling but do not define serialization or deterministic replay, so evaluator policy must determine whether portability is required.

- **Tied winners:** WIZ-DEC-TIE requires joint winners. `returns()` exposes raw scores, from which all tied maxima remain derivable, but there is no explicit winner list. This is only defective if the evaluator’s return contract requires winner utilities or identifiers.

- **Elimination/departure:** No implementation defect is assigned. The approved facts explicitly leave player departure unresolved, and the base game contains no elimination transition.

## Deterministic regression candidates

1. With `Game(4, seed=7)`, serialize the initial state, replace one ordinary deck card with a fifth Wizard, and require `state_from_data()` to raise `ValueError`.
2. Delete the undealt deck from an otherwise valid round-1 state and require rejection before any action or next-round deal.
3. Change a revealed Jester state to `phase="choose_trump"` with pending dealer choice; require rejection.
4. In a genuine revealed-Wizard state, change `pending.player` or `current_player` away from the dealer; require rejection.
5. Set `terminal=True` in a valid round-1 prediction state; require rejection.
6. Set `max_round` to anything other than `60 // players`, and test all player counts 3–6.
7. Import `phase="play"` while one prediction is `None`; require rejection.
8. Import predictions `-1` and `round_number + 1`; require rejection.
9. Import out-of-range dealer, leader, current-player, trick-player, and completed-trick winner indices; require rejection.
10. Import a partial trick with duplicate or non-clockwise actors; require rejection.
11. For fixed seeds and 3–6 players, play only legal actions through completion and assert exact 60-card conservation at every transition, round sizes `1..60/n`, no final-round trump, and final scoring before terminal.
12. If portable replay is required, load one serialized midgame state into two differently seeded `Game` objects and assert identical subsequent shuffles and states.
13. If perfect recall is required, assert that every observation after a completed trick retains its public cards, order, and winner.