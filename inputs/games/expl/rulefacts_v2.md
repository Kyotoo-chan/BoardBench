---
status: approved-for-v2-original-packet
approved_by_user: 2026-07-26
source_id: EXPL-NSFW-DE-2018-RULES
rulebook: inputs/games/expl/game_rules.pdf
sha256: f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853
scope: complete German NSFW Edition 2018 base game; 2–5 players; both pages including combinations
---

# Exploding Kittens V2 atomic rule facts

## Source register

The only gameplay source is the supplied two-page publisher PDF. It was freshly rendered completely and without cropping at 150 DPI; `game_rules_render_manifest.json` records renderer and page hashes. `claims_v2.json`, evaluator decisions, profiles, scenarios, adapters, historical artifacts and `variants/expl_clarified.txt` are not publisher sources. The historical clarified text is excluded from the V2 Original model packet.

## Atomic inventory

`claims_v2.json` is canonical: 78 atomic claims, including 66 source-clear claims. Of those, 65 are material and deterministically testable through the frozen public contract. The single-cat claim remains clear (“Einzeln sind diese Karten machtlos”) but is not hard-transition-tested because doing so would additionally assume standalone play legality.

The printed inventory is exactly 56 cards:

- 4 Exploding Kittens;
- 6 Defuses;
- 4 Attacks;
- 5 Nopes;
- 4 Skips;
- 4 Favors;
- 4 Shuffles;
- 5 See-the-Future cards;
- five cat-card titles with four copies each (20 cards).

Exact setup arithmetic:

| Players | Starting hands | Draw pile | Boxed |
|---:|---:|---:|---:|
| 2 | 16 | 35 | 5 (3 Kittens, 2 Defuses) |
| 3 | 24 | 30 | 2 Kittens |
| 4 | 32 | 23 | 1 Kitten |
| 5 | 40 | 16 | 0 |

Every player begins with seven dealt cards plus one Defuse; the pile receives `players - 1` Kittens. Only the two-player setup boxes two additional Defuses.

## Clear rule groups

- zero or more card plays followed by the turn-ending top-card draw;
- clockwise play among living players, public pile size, private hands, and legal empty hands;
- immediate Kitten reveal, undefused elimination and complete hand/Kitten discard;
- Defuse discard, secret chosen reinsertion without disturbing other cards, and individual-turn end;
- Attack assigns exactly two consecutive turns; an attacked player’s Attack passes exactly two turns onward;
- Skip ends one individual turn and consumes only one Attack debt;
- Nope cancellation, parity toggling, off-turn availability, exceptions for Kitten/Defuse, and discard retention;
- target-selected Favor transfer; Shuffle conservation; private, order-preserving See the Future;
- same-title pairs, triples, five distinct titles, and suppression of component effects in combinations;
- immediate terminal result when one survivor remains.

## Approved evaluator decisions

`decisions_v2.json` is evaluator-only and not model-facing in the Original condition:

1. Empty-handed players are illegal Favor and Pair targets.
2. With fewer than three pile cards, See the Future shows all remaining cards privately and in order.
3. Defuse is not an ordinary hand play and is legal only after drawing a Kitten.
4. If an attacked player survives by Defusing, another owed turn remains; if that player is eliminated, remaining debt expires.

## Explicitly unresolved or unscored

- voluntary death while holding Defuse;
- deterministic physical Nope priority or window-closing protocol;
- whether all action parameters, including a triple request, must be announced before a Nope window;
- a restored targeted action whose target spent its last card during the reaction chain;
- immediate retrieval of one of the five just-played combination components;
- retrieval and hand behavior of an Exploding Kitten from discard;
- source-defined shuffle/random-theft probability distributions;
- social start-player selection details.

These items cannot become Original hard failures. The Original run may declare its own assumptions. A model-facing intervention, if any, is created only after Original evaluation and only if the observed evidence warrants it.

## Approved executable matrix

After the user-requested corrections, `scenario_matrix_v2.md` and `checks/scenarios/expl_v2.json` define 38 hard scenarios: 34 clear-basis and 4 human-decision-basis. All 65 required clear claims are mapped. The player-count probe additionally performs an initial legal-action check and bounded rollout for every supported count.

On 2026-07-27, the first generated implementation exposed an evaluator-profile omission before any valid scoring: the canonical deck list had not defined which end was the top. V2.1 freezes deck state as bottom-to-top (final item is top), preview arrays as top-to-bottom, and reinsertion position as the number of cards below the Kitten. V2.2 additionally fixes evaluator timing: post-effect assertions occur after only mechanical pass/Nope reaction opportunities, and synthetic reaction fixtures align `current_player` with their declared responder. Technical envelope checks now accept positive schema versions. No game-rule expectation changed. Invalid replays are retained separately and only the corrected V2.2 replay of the final blind `v2_original_2` implementation is eligible for reporting.
