# Post-hoc canonical diagnostic comparison

This fresh run used the same canonical publisher PDF, unchanged correct component JSON, generation model (`gpt-5.6-sol`, low thinking), generation prompt, frozen evaluator, and three neutral canonical judges as the `json_clean` arm. It is a post-hoc diagnostic and is not added to the preregistered arm aggregate.

## Result

| Evidence | Diagnostic | Original `json_clean` arm |
|---|---:|---:|
| Technical gate | PASS | 3/3 PASS |
| Robustness gate | PASS | 2/3 PASS |
| Interface gate | PASS | 2/3 PASS |
| Scenarios P/F/C/U | 0/2/35/0 | 16/52/33/10 across 3 runs |
| Scenario coverage | 1.000 | mean 0.910 |
| Neutral judges | 0.42, 0.49, 0.42 | nine scores, mean 0.421 |
| Judge mean | **0.443** | **0.421** |

## Immediate diagnosis

The scenario score of zero is not evidence for 37 independent rule failures:

- 33 of the 35 crashes have the identical exception `TypeError: unhashable type: 'list'`.
- The exception originates from evaluator adapter deduplication at `checks/scenario_adapters/bohnanza.py:84`, where `dict.fromkeys(candidates)` assumes every recursively discovered state value is hashable. This implementation stores hands and fields as nested lists, which is valid Python state but violates that evaluator assumption.
- The inventory scenario reports 133 cards, while the implementation's explicit `BEANS` counts sum to the canonical 129. That mismatch also requires an evaluator/accounting audit rather than acceptance as a confirmed code defect.

The three blind judges independently give a normal result for this experiment: mean 0.443, close to the prior clean-JSON mean of 0.421. They agree that the implementation correctly captures the 129-card inventory, ordered hands, printed bean values, planting, harvesting rewards, and the broad four-phase structure. Their repeated substantive defects are instead five-player/configurable-start setup, trade/gift consent and unequal trades, private information, harvest decision ownership, and third-depletion timing.

## Conclusion

This diagnostic strengthens the concern that the very low scenario aggregates are heavily confounded by evaluator–implementation representation incompatibility. The implementations still contain real major rule defects according to all three judges, so the correct conclusion is neither “the runs are good” nor “the rulebook/JSON failed.” Before using the scenario comparison scientifically, the frozen adapter failures must be classified separately from implementation failures and replayed with a representation-safe post-hoc adapter without rewriting the original frozen results.
