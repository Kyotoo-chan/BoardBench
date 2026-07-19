# Bohnanza contract-v2 mini-study preflight

Status: **PASSED — model calls may start sequentially**

No model call or scored run existed when this report was written.

## Frozen design

One fresh generation per condition, in this order:

1. `pdf_only`
2. `json_clean`
3. `json_mutated`
4. `pdf_mutated`

Generation settings: `gpt-5.6-sol`, low thinking, low verbosity, protocol `agentic-v3.0`. One neutral judge per valid run uses the same model with medium thinking. All source, prompt, contract, profile, self-check, scenario, adapter, runner, and technical-check hashes are frozen in `inputs/games/bohnanza/contract_v2_manifest.json`.

## Token-safety gates

- Every packet contains the assigned source condition, generic contract, Bohnanza profile, prompt, and immutable self-check; it contains no rulefacts, scenarios, evaluator adapter, previous implementation, score, or review.
- `implementation.py` must pass compilation and the independent canonical self-check before evaluation.
- Contract methods, exact profile fields, JSON domain, deterministic seeded constructor, state/action roundtrips, observations, legal-action preservation, source coverage, and assumptions schema are checked.
- A failed neutral gate receives at most two evaluator-neutral repair calls. If it still fails, the study stops before launching the next condition.
- Technical checks 01–04 run again after preservation; failure stops the study.
- Each completed run is written directly under `results/scores/bohnanza/contract_v2_mini/runs/<condition>/`; experimental `outputs/` remains clean.
- Progress is atomically persisted after every valid run and every judge.

## Evaluator preflight

A hand-written infrastructure probe, not a rule implementation, passed the exact canonical self-check (`300` states, `4500` actions). All 37 contract-native scenarios executed through canonical state/action/observation data with `0 CRASH` and `0 UNTESTABLE`. The probe intentionally does not need to pass rule expectations; it proves that every fixture and selector is representable without generated-state introspection.

The contract-native adapter is regression-checked to contain no generated state attribute access, module-constant search, dataclass inspection, or raw action tuple indexing.
