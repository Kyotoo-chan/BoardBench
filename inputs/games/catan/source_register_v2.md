# CATAN V2 source register

## Assigned source condition

| Source ID | Role | Edition evidence | SHA-256 |
|---|---|---|---|
| `CATAN22-RULES` | `publisher_rulebook` | KOSMOS/CATAN GmbH; © 1995, 2022; article 68 26 82; title stem `682682_Cat_Basis34_Manual_211202` | `e0673fa93040f5b43908b215f52573878f586d26827d3a4f07c2ef8f8a947cf3` |
| `CATAN22-ALMANAC` | `publisher_companion` | Same copyright, article and production stem `682682_Cat_Basis34_Almanach_211202` | `8fe89cc65308c08104a2b2afd2f8edae24e8c608383420b044a6f35cd2c611bc` |

The primary explicitly delegates details to the companion on PDF page 2: “Benötigen Sie während des Spiels mehr Informationen, so schlagen Sie unter dem jeweiligen Stichwort … im CATAN-Almanach nach.”

## Approved scope

Illustrated beginner setup for all stated player counts, 3 and 4 players, with strict roll → trade → build phases. At three players all red pieces are removed as directed. Variable setup/Gründungsphase, the experienced merged trade/build recommendation, CATAN Assistant, expansions and remembered/web rules are excluded without cropping either PDF.

## Excluded companion candidates

- `game_almanac_base_2015.pdf`, SHA-256 `9d8d0607326f82ea7bfda11aafa5be65aaffe41f043ae996f6d72f30e92c049f`: “Regelstand Januar 2015,” not edition-matched.
- `game_almanac_bigbox_2016.pdf`, SHA-256 `0dd37693be9d898752136f6a032f224580782d7c3e79dda37fed1e0b321577a2`: Big Box 2016, not edition-matched.

## Fresh render evidence

Both assigned PDFs were freshly rendered in full at 150 DPI using `pdftoppm version 24.04.0`: four rulebook pages and 24 almanac pages. Per-page hashes are retained in `game_rules_render_manifest_v2.json` and `game_almanac_render_manifest_v2.json`. Generation will render the canonical PDFs freshly again and bind those page hashes in run evidence.
