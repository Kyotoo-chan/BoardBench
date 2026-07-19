# Bohnanza Base 2023 preflight

Status: **PASSED — one model generation may start**

No model call or scored run for this edition existed when this report was written.

## Frozen source and scope

- Publisher PDF only: `inputs/games/bohnanza_base_2023/game_rules.pdf`
- SHA-256: `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`
- Exactly 104 cards and eight bean types; no Acker-, Weinbrand-, Kaffee-, or Kakaobohnen and no component appendix.
- One generation (`gpt-5.6-sol`, low thinking), then one neutral Judge (`gpt-5.6-sol`, medium thinking).
- All method hashes and settings are frozen in `inputs/games/bohnanza_base_2023/experiment_manifest.json`.

## Approved test scope

The 31 cited scenarios cover inventory/setup, immutable hand order, all four phases, field compatibility, forced harvesting, active-only trade, arbitrary hand positions, unequal exchange, consent/gifts, received-card staging, harvesting/protection, all eight printed payout curves, recycling, third depletion, final harvest, ignored hands, scoring, and tie-breaking.

Approved human decisions are recorded in `rulefacts.md`: immediate third depletion outside phase two, hidden opponent hand identities in player observations, and off-turn harvests at stable decision boundaries.

## Zero-token validation

- Frozen manifest and packet construction pass.
- The generation packet contains only the assigned PDF and representation-only contract/profile/self-check files; no rulefacts, scenarios, adapter, previous implementation, component JSON, or reviews.
- Reachable-state probe: `300` states and `5400` actions pass canonical JSON/roundtrip checks.
- Complete-fixture probe passes every profile phase, pending consent, zone distribution, and 3/4/5-player construction.
- All 31 evaluator scenarios execute through canonical state/action data with `0 CRASH` and `0 UNTESTABLE` using the infrastructure probe.
- 33 focused regression tests pass.
- Results write directly under `results/scores/bohnanza_base_2023/base_pdf_1/`; `outputs/` remains clean.
- A neutral gate failure receives at most two repairs; persistent failure stops before judging.

The earlier four contract-v2 generations are separately retained as diagnostic-only evidence under `results/scores/bohnanza/aborted_contract_v2_prebase/`. They will not be combined with this run.
