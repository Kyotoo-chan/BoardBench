I found one major rule-fidelity contradiction and one minor terminal-state discrepancy. No critical contradiction was identified. Per the manifest, `RULES` controls gameplay; `COMPONENTS` was used only for approved inventory and yield facts.

## Major finding

### Inactive players cannot exercise the anytime-harvest right

- Fact ID: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Direct quote: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Code locations: [implementation.py:100](</C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_rule_fidelity_2sidod4s/implementation.py:100>), [implementation.py:107](</C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_rule_fidelity_2sidod4s/implementation.py:107>), [implementation.py:147](</C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_rule_fidelity_2sidod4s/implementation.py:147>)
- Expected behavior: Between atomic game steps, any player may choose to harvest one of their own legal fields, including during another player’s turn.
- Actual behavior: `legal_actions()` creates harvest actions only for `state.decision`. Every phase either reuses that single player’s `harvests` or, in phase 3, calls `_harvest_actions()` only for the selected planting player. There is no interrupt or action through which another owner can harvest. Supplying another player number manually also fails the legality check in `apply_action()`.
- Impact: An inactive player can be prevented from harvesting before subsequent trades, planting steps, draws, or game end. This changes legal choices and can affect forced harvests, field composition, and scoring.
- Severity: Major
- Confidence: High

## Minor finding

### Final harvesting does not apply the two-Ackerbohne field-unlock effect

- Fact ID: `ACKER-01`, together with `END-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 11
- Direct quote: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
- Code location: [implementation.py:182](</C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_rule_fidelity_2sidod4s/implementation.py:182>)
- Expected behavior: Harvesting exactly two Ackerbohnen unlocks the third field when it is absent, including when fields are harvested at game end.
- Actual behavior: `_finish()` treats two Ackerbohnen as earning zero coins and clears the field, but never sets `third_field[p]` or appends the third field.
- Impact: Terminal state is not an exact record of the prescribed harvest, although the missing field has no subsequent gameplay or scoring effect.
- Severity: Minor
- Confidence: High

## Open question

- `SET-03` requires a chosen/configured start player. The implementation permanently treats player 0 as the start player ([implementation.py:46](</C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_rule_fidelity_2sidod4s/implementation.py:46>), [implementation.py:197](</C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_rule_fidelity_2sidod4s/implementation.py:197>)). Are player IDs contractually assigned relative to the chosen start player? If so, this is a valid representation; if IDs are externally fixed, start-player selection is missing.

Covered rule areas: 4–5-player setup, 129-card inventory, ordered hands, fields, all four turn phases, bilateral trading and gifts, mandatory planting, variant drawing, reshuffling and depletion, harvest protection and yields, Ackerbohne rewards, game end, scoring, hand visibility, and tie-breaking.

Uncovered or intentionally unresolved: social negotiation and voluntary disclosure, impossible short-draw states identified as unscored by the approved facts, and physical non-bean component quantities.

Qualitative conclusion: The model is broadly faithful and handles the difficult Ackerbohne and third-depletion rules well. Its principal fidelity gap is structural: the decision model does not permit the rulebook’s out-of-turn harvesting right.
