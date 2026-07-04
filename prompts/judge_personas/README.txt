BoardBench judge personas — overlays on prompts/llm_judge_review.md

Each file is appended after the base judge prompt in a packet.
Run: python checks/run_judge_personas.py --persona casual_beginner --code outputs/expl_gpt_ag.py --rules inputs/games/exploding_kittens/game_rules.pdf

| file | purpose | good for |
|------|---------|----------|
| casual_beginner.md | first-time player UX | action explosion, naming, information_state |
| strict_rules_lawyer.md | literal rulebook only | assumption audit |
| qa_engineer.md | testability | checks/07 scenario ideas |
| adversarial_skeptic.md | find break paths | logic holes |
| benchmark_harness.md | rollout/pair/OS fit | EK 287-start-actions class problems |
| mismatch_detector.md | wrong game vs rulebook | calibration (ek×hav, aba×ek) |

Not an oracle: personas add lenses; deterministic checks + hand-test stay primary.
