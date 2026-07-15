# BoardBench scenario schema v3

A scored scenario must be traceable, deterministic where material, and explicit about human adjudication. Each suite declares a `rubric_version`; machine-readable results retain suite, adapter, and implementation hashes.

```json
{
  "id": "GAME-R01-stable-name",
  "fact_ids": ["TURN-01"],
  "basis": "clear",
  "source": {"page": 1, "quote": "Direct rulebook quote ..."},
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
```

`basis` is `clear` or `human_decision`. Unresolved assumptions do not become scored scenarios.

## Outcomes

- `PASS`: evaluated expectation holds.
- `FAIL`: evaluated expectation is contradicted.
- `CRASH`: a reached legal transition or observation raises unexpectedly.
- `UNREACHED`: exploratory public search did not find the requested action.
- `UNTESTABLE`: the configured API/adapter cannot construct or observe the evidence.

Scores use `PASS+FAIL+CRASH`; coverage reports that evaluated denominator over all scenarios. Keep clear-rule and human-decision scores separate.

## Action selectors

Supported selectors include exact `name`, legacy `normalized`, `select`, `index`, `contains_any`, `contains_all`, and `contains_all_groups`. `prefer_contains_all_groups` chooses a more specific semantic action when one implementation combines choices into one action while another uses a later phase.

Use source-visible labels and list known variant labels. Do not rely on translated or remembered names.

## Intermediate phases

An expectation is checked after the configured `settle` steps. Use these only for mechanical intermediate phases such as all-player reaction passes or a required donation. The scenario must say exactly when the rule expectation becomes observable.

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

LLM- or search-proposed traces remain exploratory until replayed, human-approved, and added to a later frozen evaluator version.
