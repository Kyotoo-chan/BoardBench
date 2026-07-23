# CATAN neutral judge preflight v2

The first three judge calls used the globally frozen prompt SHA-256 `d24903a2498d09dc2950807af05cdbc9b5848d1e026931477c341a8af809dec2`. That prompt contained a Bohnanza-specific sentence about a “five-card combination retrieving one of its own just-discarded components.” This is irrelevant to CATAN and plausibly biased one trade finding.

The three raw v1 reviews/events/usages are retained with `judge_v1_contaminated_*` names and excluded from the reported neutral mean.

Replacement neutral prompt:

- path: `method/llm_judge_review_v2.md`
- SHA-256: `137adad3a810743ca78823fa93200900da2ffa5bbc730e1c06d8c5623ef827ae`
- change: remove only the game-specific sentence; retain evidence, severity, output, blindness, source, model, and thinking requirements.

Three fresh mutually blind judges use the unchanged judge packet, implementation, sources, approved facts, model `gpt-5.6-sol`, thinking `medium`, and attached 28 fresh source-page images. They receive no v1 reviews or evaluation results.
