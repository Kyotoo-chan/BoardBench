# Rulebook analysis

Use only the supplied rulebook. Do not write code or use remembered rules.

Return a concise implementation brief with:

1. **Game type:** players, turn structure, chance, private information, scoring.
2. **State:** public, private, chance, and history fields actually required.
3. **Flow:** setup, phases, player changes, forced actions, end conditions.
4. **Actions:** canonical action grammar and validation rules.
5. **Transitions:** what each action changes.
6. **Terminal/returns:** every ending and expected return vector.
7. **Ambiguities and risks:** page + direct quote, why implementation depends on it, and `clear|ambiguous|not specified`.

Do not silently resolve an ambiguity. Prefer a small faithful scope over invented completeness.
