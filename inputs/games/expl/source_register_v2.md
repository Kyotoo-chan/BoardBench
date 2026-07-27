# Exploding Kittens V2 source register

## Assigned condition source

| Source ID | Role | Authorship | Artifact | SHA-256 | Edition / scope evidence | Condition |
|---|---|---|---|---|---|---|
| `EXPL-NSFW-DE-2018-RULES` | `publisher_rulebook` | Exploding Kittens | `game_rules.pdf` | `f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853` | Cover states “NSFW Edition”, German rules, copyright 2018, 2–5 players, 56 cards; both supplied pages retained | Original PDF-only |

No publisher companion is required or assigned. No component appendix is assigned. `variants/expl_clarified.txt` is a historical pilot intervention and is excluded from the V2 Original source packet.

## Model-facing render

The complete two-page PDF was freshly rendered without cropping at 150 DPI. Manifest: `game_rules_render_manifest.json`.

- Renderer: `pdftoppm version 24.04.0`
- Page 1 SHA-256: `9ba1026ff166677d3c0e354837966d1bd25594fc7af03067deaf1ee856cf78fb`
- Page 2 SHA-256: `be12dbff635adee26efc3d89b36ce790e55e4b15af226f240dde0d45bda1dfea`

Extracted text, legacy facts, historical implementations, historical clarified text and evaluator decisions are derived or excluded artifacts and are not publisher rule sources.

## Targeted clarified condition

After the committed eligible Original run exposed an empty-target deadlock, the Clarified condition keeps the publisher PDF byte-identical and adds only `clarifications_v2.json` (`experimenter_clarification`, SHA-256 `03f295bb413faffb35fd313c20ee46d14aabbc1b40f66db2bc274bca3f6c6a89`). It resolves `EXPL-X-EMPTY-TARGET`: Favor and Pair require a living opponent with at least one card. It does not restate the clear publisher rule requiring an eliminated player's remaining hand and Kitten to enter discard.
