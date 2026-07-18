# BoardBench rule review

Review one generated module against the complete supplied source condition and its provenance labels. Do not edit code, run generic checks, or use outside game knowledge.

## Evidence rule

For every `critical` or `major` finding include:

- canonical fact ID;
- evidence type: `rule_quote`, `user_observation`, or `human_decision`;
- source ID, stable locator (PDF page or JSON Pointer), and exact source evidence;
- conflicting code symbol or transition;
- expected versus implemented behaviour.

Verify the complete approved fact before scoring. Do not penalize behaviour that the approved fact permits, including a five-card combination retrieving one of its own just-discarded components. If the packet does not decide the issue, use `question`; do not treat remembered rules as truth. Keep adjudication-dependent deviations visibly separate from contradictions of clear printed rules.

Severity:

- `critical`: core game cannot complete reliably, common crash/deadlock, or fundamentally wrong winner/game;
- `major`: material setup, action, phase, chance, information, or terminal rule is absent/contradicted;
- `minor`: localized issue unlikely to change core flow or winner;
- `question`: rulebook evidence is insufficient or ambiguous.

## Review

Check setup, turn flow, legal actions, transitions, chance/private information, terminal conditions, returns, and unsupported assumptions.

Return:

1. `score: 0.0-1.0` and `confidence: low|medium|high` with a brief rationale;
2. findings ordered by severity;
3. compact rule-area coverage table;
4. missing deterministic scenarios;
5. material questions for a human.

End exactly with:

```text
score: <0.0-1.0>
confidence: low|medium|high
critical_issues: <number>
major_issues: <number>
minor_issues: <number>
needs_rulebook_clarification: true|false
needs_code_change: true|false
needs_more_tests: true|false
```
