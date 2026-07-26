# Abalone V2 original-condition findings

- Agentic gate, technical gate, robustness, interface and player counts: PASS.
- Clear-basis scenarios: 32/33.
- Human-decision-basis scenarios: 5/5.
- Evaluated coverage: 38/38.
- Neutral Judges: 0,86 / 0,90 / 0,84; mean 0,867, sample SD 0,031.

Confirmed defect: `ABAL-R01` found 13 black and 13 white marbles instead of the Figure-1 requirement of 14 each. All other configured scenarios passed. This is a clear-rule implementation defect, not a source gap.
