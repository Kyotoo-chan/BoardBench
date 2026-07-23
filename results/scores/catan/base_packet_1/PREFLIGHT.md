# CATAN base packet 1 — evaluation preflight

- **status:** frozen before evaluation
- **frozen at:** 2026-07-23T13:36:29.636950+00:00
- **source condition:** matching official German 2022 Spielanleitung + explicitly required 2022 Almanach
- **game scope:** fixed four-player beginner setup; strict roll → trade → build
- **implementation:** `outputs/catan_codex_ag.py`
- **implementation commit:** `3508766`
- **preparation commit:** `ff54365`
- **implementation model:** `gpt-5.6-sol:low`
- **judge model:** `gpt-5.6-sol:medium`, three independent neutral blind reviews

## Frozen hashes

| Label | Role | Path | SHA-256 |
|---|---|---|---|
| `CATAN22-RULES` | `publisher_rulebook` | `inputs/games/catan/game_rules.pdf` | `e0673fa93040f5b43908b215f52573878f586d26827d3a4f07c2ef8f8a947cf3` |
| `CATAN22-ALMANAC` | `publisher_companion` | `inputs/games/catan/game_almanac.pdf` | `8fe89cc65308c08104a2b2afd2f8edae24e8c608383420b044a6f35cd2c611bc` |
| `rulefacts` | `approved_facts` | `inputs/games/catan/rulefacts.md` | `57c2157175e1851b1ca562a11c02c6429ffd999694602975a213a46e39f34b22` |
| `environment_profile` | `representation_profile` | `inputs/games/catan/environment_profile.json` | `24333cabf21f9e65e2c23bcb50cb8d850ff06c88257045431b7ae9f5b29bc15c` |
| `scenario_suite` | `rule_fidelity_evaluator` | `checks/scenarios/catan.json` | `b7a4f653376d18d3d1ad1dd12aff596b0308946ee69602cf613c409848d26cfe` |
| `scenario_adapter` | `evaluator_adapter` | `checks/scenario_adapters/catan.py` | `fce085d7dd545793603260f85dd8157d63674ac4fe8c4a70e0f400253de83454` |
| `scenario_runner` | `evaluator_runner` | `checks/run_scenarios.py` | `d852145a60ab361412c7e3847ec3a2e49297ddba9a2bf64ef4b7ba7d87e6f762` |
| `check_runner` | `grouped_check_runner` | `checks/run_checks.py` | `14815891c78091e7b7a9784ca0bb811c453047e5ab57248da905c450390f0b1d` |
| `judge_prompt` | `judge_method` | `inputs/prompts/llm_judge_review.md` | `d24903a2498d09dc2950807af05cdbc9b5848d1e026931477c341a8af809dec2` |
| `environment_contract` | `representation_contract` | `inputs/prompts/environment_contract.md` | `eba8a3aa67b2770d46a3da5a008e32314dd80d8b35b56c7c50dcb3a9ff280570` |
| `implementation` | `generated_module` | `outputs/catan_codex_ag.py` | `bcd19e4a0a9b9f384370572351a37b72f39e31354a9cc70e0aeaba9cde765122` |
| `agentic_evidence` | `generation_evidence` | `outputs/catan_codex_ag_agentic.json` | `89ac655a7610b97fc6e30d431cdb2c09062e292af64628c975ccb356eba83e99` |
| `assumptions` | `source_audit` | `outputs/catan_codex_ag_assumptions.json` | `e19728ba1d610918ac8d1402a7fc7578368b27b942f99b75e8ea2b605c0c8931` |

## Evidence separation

1. Technical gate: checks 01–04.
2. Runtime robustness: check 05.
3. Interface: check 06.
4. Rule fidelity: cited version-3 scenarios; `PASS+FAIL+CRASH` only, with coverage reported separately.
5. Independent review: three neutral source-only judges; arithmetic mean and sample SD remain separate from machine evidence.

Judges receive both assigned publisher PDFs, provenance labels, approved facts, and the generated module. They do not receive scenario expectations, machine results, prior reviews, variants, or scores. Resource-bank shortage cases remain unscored by prior approval. No evaluator result is available in this frozen packet.
