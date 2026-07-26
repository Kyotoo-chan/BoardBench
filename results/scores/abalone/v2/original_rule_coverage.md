# Rule coverage

| Source section / named rule | Implementing symbol | Source-only probe or omission | Assumption |
|---|---|---|---|
| Ziel des Spieles; Wer gewinnt? | `apply_action`, `is_terminal`, `returns` | Push six opposing marbles out; terminal exposes no actions | — |
| Vorbereitung / Abbildung 1 | `initial_state` | 14 black and 14 white marbles placed as pictured; black starts | A-01 |
| Der Spielablauf | `_groups`, `_legal_move`, `legal_actions`, `apply_action` | Alternating one movement; groups of 1–3; six directions; destination hollow free | A-02 only for an otherwise actionless fixture |
| Abbildung 2: Bewegung in gerader Linie | `_legal_move`, `apply_action` | Inline translation into the next hollow | — |
| Abbildung 3: Bewegung zur Seite | `_legal_move`, `apply_action` | Broadside translation requires all next hollows free | — |
| “Ist eine Bewegung ausgeführt…” | immutable successor construction in `apply_action` | One action produces exactly one successor | — |
| Sumito | `_legal_move`, `apply_action` | Strict numerical advantage; 2–1, 3–1, and 3–2; at most two opponents | — |
| Sumito restrictions / Abbildung 5 | `_legal_move` | Only inline, directly adjacent, with empty hollow or edge behind; blocked/non-collinear cases rejected | — |
| Patt; 1–1, 2–2, 3–3 | `_legal_move` | Equal opposing counts cannot push | — |
| Abbildung 7: Patt auflösen | `_legal_move` | A legal attack may start on another line/angle; no forced attack | — |
| Hinausschieben / Abbildung 8 | `apply_action` | Opponent moved beyond board increments mover's capture count | — |
| Gegen die Zeit | not implemented | Optional clock examples provide no required timing procedure or evaluator field | — |
| Chance/private information | `Game.__init__`, canonical serializers | No chance or private information appears in the supplied rules; seed is retained as representation metadata | — |
