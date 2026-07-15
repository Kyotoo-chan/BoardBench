# Clarified-rulebook diagnostic run

`expl_clarified_r1` tests a new source condition: the faithful TXT followed by a visibly labelled appendix of 21 binding, previously approved interpretations. The appendix uses natural rule language and contains no scenario IDs, fixtures, expected traces, check code, or repository paths.

This is not presented as the publisher's original rulebook. It is an **implementation-specification condition** designed to test whether failures remain after known ambiguity is removed.

## Input and protocol

| Item | Value |
|---|---|
| Source | `inputs/games/expl/variants/expl_clarified.txt` |
| Source SHA-256 | `1bd75b96c9740cd92bc9cc8582370676e430ca6ba81387ce82f07b64f20bbcf7` |
| Closest baseline | Faithful TXT r2 |
| Protocol | `agentic-v2.1` |
| Model | `gpt-5.6-sol:medium` |
| Rule coverage audit | required, 72 lines |
| Repairs | 0 |
| Agent self-check | pass |
| Independent gate | pass |

## Results

| Evidence group | Result |
|---|---:|
| Technical gate 01–04 | 4/4 |
| Runtime robustness | 100/100, score 1.000 |
| Interface | 18,662/18,662 names, score 1.000 |
| Clear deterministic scenarios | 10/10 |
| Approved human-decision scenarios | 7/7 |
| Scenario coverage | 17/17, 100% |
| Judge scores | 0.99, 0.95, 0.88 |
| Judge mean (n=3) | 0.940 |
| Generated Python | 300 lines |

The first raw run used evaluator `expl-v2.4` and preserved `2 PASS / 15 UNTESTABLE`: the adapter did not know state fields `active` and `turns_owed`. Version `expl-v2.5` constructed the state and produced `15 PASS / 2 FAIL`; those two apparent Defuse failures came from requiring a separate action named Defuse, while this implementation correctly consumes mandatory Defuse automatically and asks only for the explicit reinsertion position. Version `expl-v2.6` accepts both valid phase designs and yields:

```text
PASS=17 FAIL=0 CRASH=0 UNREACHED=0 UNTESTABLE=0
```

Every historical result is retained separately.

## Closest controlled comparison

| Evidence | Faithful TXT r2 | Clarified TXT r1 |
|---|---:|---:|
| Protocol | agentic-v2 | agentic-v2.1 |
| Robustness | 1.000 | 1.000 |
| Interface | 1.000 | 1.000 |
| Clear rules | 9/10 | 10/10 |
| Human decisions | 4/7 | 7/7 |
| Judge mean | 0.693 | 0.940 |
| Python lines | 365 | 300 |

The clarified implementation fixes every deterministic baseline failure: mandatory Defuse, five-card self-retrieval, and empty Favor/pair targets. This is strong diagnostic evidence that explicit wording can remove translation failures.

It is not yet a clean causal estimate because both source precision and protocol changed (`agentic-v2` to `agentic-v2.1`) and each cell has one implementation. A strict source-only experiment should generate repeated faithful and clarified TXT implementations under the same frozen protocol.

## What the judges still exposed

Passing the current 17 scenarios does not mean the specification is complete. The blind reviewers identified one material temporal candidate and several uncovered questions:

1. **Five-card/Nope timing:** the implementation chooses the discard retrieval only after the Nope window. Approved interface facts say targets and parameters should be announced before reactions, but the clarification appendix did not state this explicitly and no current scenario tests it.
2. **Preview knowledge after Shuffle:** previously stored top-card information may remain visible after the deck changes.
3. **Target spends its final card during a Nope chain:** target legality was true when announced but may become impossible to resolve.
4. **Deck exhaustion after a discarded Kitten is retrieved:** the original physical invariant may no longer hold in an executable environment.

These are not silently converted into failures. They require deterministic traces, user confirmation where material, and a later rubric version.

## Workflow implication

The result supports a scalable three-layer workflow:

1. **Canonical source:** preserve the publisher's PDF or original TXT and its hash.
2. **Approved executable interpretation:** record ambiguity decisions separately and create deterministic hidden scenarios.
3. **Clarified-source experiment:** append only approved natural-language clauses, regenerate blindly, and test whether the previously observed failures disappear.

If failures disappear, they are evidence of source underspecification or wording sensitivity. If they remain despite an explicit clause, they are stronger evidence of model translation failure. New judge findings feed back as candidates, never as automatic truth.

## Input formats for other games

BoardBench accepts both PDF and TXT:

- Publisher PDF → canonical PDF; optionally create a separately hashed faithful TXT extraction as a format condition.
- Native text rules → canonical TXT; do not manufacture a PDF.
- Clarified/omitted/vague/false versions → deterministic script, separate path/hash/condition, never overwrite canonical or historical inputs.

The policy is documented in `inputs/README.md`. Exploding Kittens transformations are reproducible in `generation/prepare_expl_variants.py` and frozen in `inputs/games/expl/variants/manifest.json`.

## Artifacts

- `metrics.json` — compact result record.
- `expl_clarified_r1_scenarios_v2_5.json` — preserved intermediate evaluator result.
- `expl_clarified_r1_scenarios_v2_6.json` — current deterministic result.
- Experiment commit `17c7067` — raw implementation, coverage audit, checks, events, usage, and three reviews.
