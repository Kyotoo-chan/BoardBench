# Wizard base PDF evaluation

## Summary

One isolated `gpt-5.6-sol:low` implementation was evaluated against the approved Wizard Version 1.0 base-game packet. The environment passed every technical, rollout, and interface check. It passed 20 of 21 cited scenarios with full evaluated coverage. All three mutually blind neutral judges independently identified the same major Wizard-led trick defect and each scored the implementation `0.86` with high confidence.

No implementation was repaired after evaluation. This report preserves the evaluated code unchanged.

## Evidence groups

| Group | Result |
|---|---:|
| Agentic pre-evaluation gate | PASS |
| Technical checks 01–04 | 4/4 checks; 12/12 units |
| Runtime robustness 05 | 100/100 rollouts |
| Interface 06 | 223904/223904 action-language checks |
| Clear cited scenarios | 11/11 PASS |
| Human-decision scenarios | 9/10 PASS |
| Scenario coverage | 21/21 evaluated (100%) |
| Overall cited scenarios | 20 PASS, 1 FAIL, 0 CRASH |
| Neutral judge scores | 0.86, 0.86, 0.86 |
| Judge mean (n=3) | 0.86; sample SD 0.00 |

These groups are not combined into one correctness score.

## Confirmed rule defect

### Wizard-led tricks can incorrectly acquire a suit obligation

- **Severity:** major; independently reported by all three neutral judges and the rule-fidelity persona.
- **Fact:** `WIZ-WIN-02`, `WIZARD-RULES`, PDF p. 2.
- **Source evidence:** “Wird ein Stich mit einer Zaubererkarte eröffnet, dann dürfen die folgenden Lehrlinge beliebige Karten abwerfen ... Der Stich geht in jedem Fall an den ersten Zauberer.”
- **Code:** `outputs/wizard_codex_ag.py:150-151` assigns `led_suit` whenever a later ordinary card appears while `led_suit` is `None`; `legal_actions` at lines 127–130 then requires that suit when available.
- **Expected:** after a Wizard opens the trick, every later player may play any card and no ordinary card creates a follow-suit obligation.
- **Actual:** the first later ordinary card can create a suit obligation for remaining players.

The existing first-Wizard winner scenarios still pass because winner selection correctly favors the first Wizard. The uncovered defect concerns later players’ legal actions within that same trick.

## Scenario deviation tied to an approved decision

`WIZ-R14-jester-wizard-keeps-trick-colorless` failed. After `Narr → Zauberer → zwerge_rot:7`, the implementation set `led_suit` to `zwerge_rot`; approved decision `WIZ-DEC-JESTER` requires the trick to remain colorless when a Wizard appears before any ordinary colored card. This is reported separately from the printed clear-rule score.

## Independent review

All neutral judges reported:

- score `0.86`;
- high confidence;
- zero critical issues;
- one shared major Wizard-led trick issue;
- code change required.

One judge additionally raised a minor imported-state inventory concern. The executable-systems persona expanded this into several state-import invariant concerns. These remain separate interface/robustness signals rather than confirmed rule failures: the contract deliberately requires reconstruction of complete unusual evaluator fixtures and does not authorize rejecting them merely for being unreachable through ordinary play.

The ambiguity persona catalogued source omissions and ambiguities. The approved facts already expose the material decisions used by this evaluation; persona findings are not averaged into the neutral judge score.

## Generation and resource evidence

- Generation model: `openai-codex/gpt-5.6-sol`, thinking `low`.
- Neutral/persona judge model: `gpt-5.6-sol`, thinking `medium`, verbosity `low`.
- Implementation repairs: `0`.
- Evaluator-neutral infrastructure corrections before evaluation: `1` (fixture-check helper shadowing only).
- Calls recorded: `7` (one generation, three neutral judges, three personas).
- Provider time: `1453.078 s`.
- Input tokens: `1,017,020`; cached input tokens: `899,072`.
- Output tokens: `41,508`; reasoning tokens: `18,182`.
- Actual subscription cost: unavailable.
- API-equivalent estimate from recorded tokens: `$2.80`.
- Implementation size: `262` lines.

## Provenance

- Source: `inputs/games/wizard/game_rules.pdf`
- Source SHA-256: `167254a64b0866266746833c0b98836db51c08171b5b96e25f7461d5bf3dee79`
- Generated module: `outputs/wizard_codex_ag.py`
- Scenarios: `checks/scenarios/wizard.json`
- Result profile: `results/scores/wizard/base_pdf_1/result.json`
- Derived card: `results/scores/wizard/base_pdf_1/result.md`
- Raw evaluation evidence: `results/scores/wizard/base_pdf_1/raw/`

Git preserves the pre-evaluation generation commit. Any future code correction requires a new generation/run and must not rewrite this evaluated result.
