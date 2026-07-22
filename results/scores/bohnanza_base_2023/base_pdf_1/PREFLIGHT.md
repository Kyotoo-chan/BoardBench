# Bohnanza Base 2023 final preflight

Status: **PASSED**

## Frozen condition

- Publisher PDF only: `inputs/games/bohnanza_base_2023/game_rules.pdf`
- SHA-256: `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`
- 104 cards, eight bean types, no component appendix
- One accepted generation (`gpt-5.6-sol`, low) and one Judge (`gpt-5.6-sol`, medium)

## Verified before the accepted run

- The packet contained the exact frozen implementation prompt, PDF, representation contract/profile, and two evaluator-neutral self-checks.
- It contained no rulefacts, scenarios, adapter, component JSON, previous implementation, or review.
- The full 14-method public/canonical API gate passed the infrastructure probe.
- The complete rare-state fixture gate passed for every phase and 3/4/5-player construction.
- All 31 scenario fixtures were representable through the canonical contract with zero crash/untestable outcomes in the infrastructure probe.
- The manifest and every infrastructure/source hash matched.
- `outputs/` remained clean; artifacts were written under this result directory.

Rejected setup attempts and the obsolete pre-base mini-study are intentionally absent from the current tree. Their historical commits remain in Git but they are not study results.
