# Rulebook to BoardBench scenario candidates

Extract candidate black-box scenarios for `checks/run_scenarios.py` from the assigned source packet.

Rules:

- Use only the assigned sources; do not use remembered or web game knowledge.
- Every scenario needs a source ID, positive PDF page or JSON Pointer, and direct evidence. When an expectation genuinely combines pages or assigned sources, include `supporting_sources` with the same locator/quote shape.
- Mark ambiguous rules as questions instead of silently choosing an interpretation.
- Prefer observable assertions through the public BoardBench API: current player, terminal state, returns, absolute/relative legal-action count (`legal_action_count` / `legal_action_delta`), exact action name, or normalized action name.
- Start with setup, ordinary turn flow, occupied/illegal targets, and terminal conditions.
- For every card game, include cited inventory facts and a scenario that checks the exact total and per-card-type counts after setup; mark only genuinely unobservable portions `not_testable`.
- Do not inspect or mutate private fields of a generated state.
- A human or independent second model must validate quotes and expected values before the scenario becomes benchmark evidence.

Return:

1. a short list of atomic rule facts (`id`, page, quote, interpretation, ambiguity status),
2. JSON candidates matching the version-3 format in `checks/scenarios/README.md`,
3. rules that cannot be tested through the current public API and why.
