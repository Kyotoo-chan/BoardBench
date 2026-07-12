# Rulebook to BoardBench scenario candidates

Extract candidate black-box scenarios for `checks/run_scenarios.py` from the provided rulebook.

Rules:

- Use only the provided rulebook; do not use remembered game knowledge.
- Every scenario needs a page number and a direct quote.
- Mark ambiguous rules as questions instead of silently choosing an interpretation.
- Prefer observable assertions through the public BoardBench API: current player, terminal state, returns, absolute/relative legal-action count (`legal_action_count` / `legal_action_delta`), exact action name, or normalized action name.
- Start with setup, ordinary turn flow, occupied/illegal targets, and terminal conditions.
- Do not inspect or mutate private fields of a generated state.
- A human or independent second model must validate quotes and expected values before the scenario becomes benchmark evidence.

Return:

1. a short list of atomic rule facts (`id`, page, quote, interpretation, ambiguity status),
2. JSON candidates matching the version-1 format used in `checks/scenarios/havannah.json`,
3. rules that cannot be tested through the current public API and why.
