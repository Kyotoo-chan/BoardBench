# Rulebook inputs

BoardBench accepts exactly one active canonical source as `inputs/game_rules.pdf` or `inputs/game_rules.txt`.

- Use PDF when the publisher supplies PDF. Archive and hash the original bytes before extraction.
- Use TXT when text is the original source. Do not manufacture a PDF.
- A faithful TXT extracted from PDF is a separate input-format condition, not a replacement for the PDF.
- Clarified, omitted, vague, anonymized, or false-rule texts are separate experimental conditions.

Derived conditions must be created by a committed deterministic script, listed with paths and SHA-256 hashes in a manifest, and frozen before generation. Never overwrite the canonical source or an earlier experimental artifact. If extraction tooling changes bytes, retain the earlier extraction rather than silently regenerating it.

For the Exploding Kittens study, `generation/prepare_expl_variants.py` creates the declared variants under `inputs/games/expl/variants/`. `expl_clarified.txt` is the faithful TXT plus a visibly labelled normative appendix of approved interpretations. It tests whether an explicit natural-language specification is translated correctly; it is not presented as the publisher's original rulebook.

The normal reusable workflow evaluates the incoming canonical rulebook first. A clarified appendix is optional follow-up evidence after material weaknesses are approved. Negative variants are calibration controls, not required for every game. Each condition keeps its own hash and per-rulebook result profile.
