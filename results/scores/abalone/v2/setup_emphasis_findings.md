# Abalone V2 setup-emphasis findings

- Agentic gate, technical gate, robustness, interface and player counts: PASS.
- Clear-basis scenarios: 33/33.
- Human-decision-basis scenarios: 4/5.
- Evaluated coverage: 38/38.
- Neutral Judges: 0,80 / 0,93 / 0,95; mean 0,893, sample SD 0,081.

The setup emphasis fixes `ABAL-R01`. The new implementation fails `ABAL-R19`: no forced pass is offered when the active player has no legal movement. All three Judges confirm that deviation. One Judge proposes duplicate move serializations as an additional regression candidate; the frozen deterministic uniqueness scenario passes, so it is not retroactively scored.
