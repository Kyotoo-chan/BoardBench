# BoardBench scenario schema v4

A scored scenario must be traceable, deterministic where material, and explicit about human adjudication. Each suite declares a `rubric_version`; machine-readable results retain suite, adapter, and implementation hashes. New version-4 suites also declare `claim_inventory`, a repository-relative JSON file containing atomic `clear`, `ambiguous`, `missing`, `conflicting`, or `untestable` claims with boolean `material` and `testable` fields.

```json
{
  "version": 4,
  "claim_inventory": "inputs/games/game/claims.json",
  "scenarios": [
    {
      "id": "GAME-R01-stable-name",
      "fact_ids": ["TURN-01"],
      "basis": "clear",
      "source": {"source_id": "RULES", "page": 1, "quote": "Direct rulebook quote ..."},
      "fixture": {},
      "initial": {},
      "steps": [
        {
          "action": {"contains_any": ["source-visible action label"]},
          "settle": [],
          "expect": {}
        }
      ]
    }
  ]
}
```

`basis` is `clear` or `human_decision`. `fact_ids` are atomic claim IDs from the inventory. Every deterministic, material, testable clear claim needs a scenario or a non-empty `coverage_exception`; exceptions remain outside the hard-coverage numerator. Unresolved assumptions do not become clear-basis scenarios. Ambiguous, missing, or conflicting claims may support human-decision-basis scenarios after a decision is approved. Source evidence uses either a positive PDF `page` or an RFC 6901 `json_pointer`; `quote` contains the cited text or compact JSON fragment. When one expectation genuinely combines multiple pages or assigned sources, add `supporting_sources` as a list of additional source objects with the same locator/quote shape; do not compress multi-page evidence into a false single-page citation.

## Outcomes

- `PASS`: evaluated expectation holds.
- `FAIL`: evaluated expectation is contradicted.
- `CRASH`: a reached legal transition or observation raises unexpectedly.
- `UNREACHED`: exploratory public search did not find the requested action.
- `UNTESTABLE`: the configured API/adapter cannot construct or observe the evidence.

Basis pass rates use `PASS+FAIL+CRASH`; scenario evaluated coverage reports that denominator over all scenarios. Keep clear-basis and human-decision-basis rates separate. The runner does not emit a mixed correctness score. Version-4 results additionally report claim-to-scenario mapping and evaluated-claim coverage. Mapping is not proof that every clause was asserted; the approved matrix and non-empty scenario checks remain auditable evidence.

## Action selectors

Supported selectors include exact `name`, legacy `normalized`, `select`, `index`, `contains_any`, `contains_all`, and `contains_all_groups`. `prefer_contains_all_groups` chooses a more specific semantic action when one implementation combines choices into one action while another uses a later phase.

Use source-visible labels and list known variant labels. Do not rely on translated or remembered names.

## Intermediate phases

An expectation is checked after the configured `settle` steps. Use these only for mechanical intermediate phases such as all-player reaction passes or a required donation. The scenario must say exactly when the rule expectation becomes observable.

## Contract-v2 boundary

New generations expose BoardBench-owned JSON-safe state/action/observation data through `state_to_data`, `state_from_data`, `action_to_data`, `action_from_data`, and `observation_to_data`, using the frozen per-game `environment_profile.json`. New scenario adapters may use only those methods plus the original public `Game` API; generated attributes, tuple positions, module constants, private helpers, and guessed aliases are nonconforming evaluator access. Historical adapters remain `legacy-introspective`, and post-hoc compatibility replays must use a new rubric/adapter hash without overwriting frozen results.

## Deterministic adapters

A suite may declare:

```json
{"adapter": "checks/scenario_adapters/<game>.py"}
```

The adapter exposes:

```python
def setup(module, game, fixture): ...
def check(module, game, state, expected): ...
```

It may translate a semantic fixture into implementation state and expose generic observations. It must not encode the expected game-rule result. Freeze its hash with the facts, suite, runner, and judge prompt before a main study.

LLM- or search-proposed traces remain exploratory until replayed and human-approved. Approved corrections update the current evaluator; Git and result hashes retain provenance.
