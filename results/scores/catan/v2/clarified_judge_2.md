## Assessment

`score: 0.78`, `confidence: high`

The module implements most of the approved beginner game correctly, including illustrated 3/4-player setup, production, trading, construction, robber flow, development effects, privacy, scoring, and terminal returns. Three material defects remain: one clear turn-timing contradiction, stale Longest Road state after route interruption, and one deviation from the approved discard-escrow decision.

## Findings

### Major — Development cards cannot be played before rolling

- Canonical fact ID: `CAT-C-DEV-ANYTIME`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`, PDF page 2
- Exact evidence: “zu einem beliebigen Zeitpunkt seines Zuges (auch vor dem Würfeln) eine seiner Entwicklungskarten ausspielen.”
- Conflicting code: `Game.legal_actions`, especially the phase gate at lines 164–176.
- Expected: The active player may play one eligible Knight or progress card before rolling.
- Implemented: Development actions are generated for discard, robber, trade, offer, and build phases, but not for `phase == "roll"`. The sole pre-roll action is `roll_dice`.
- Impact: Valid tactical plays—and potentially an immediate Largest Army victory—are unavailable at a source-explicit timing point.

### Major — An opponent settlement does not update Longest Road

- Canonical fact IDs: `CAT-C-LR-OPP-BLOCK`, with downstream effects on `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, and `CAT-C-LR-VACANT-TIE`
- Evidence type: `rule_quote`
- Source: `CATAN22-ALMANAC`, PDF page 8
- Exact evidence: “Wird eine Straße durch eine fremde Siedlung unterbrochen”
- Conflicting code: `Game.apply_action` → `build_settlement` at lines 326–328; `_update_longest` is called after road placement at line 325 but not after settlement placement.
- Expected: Placing an opponent settlement on a route vertex immediately interrupts that route and recomputes ownership, including incumbent and vacant-tie rules.
- Implemented: The board building changes, but `longest_road_owner` and `longest_road_length` remain stale until a later road placement.
- Impact: Visible scores and the special-card owner can remain wrong across turns, potentially producing an incorrect victory.

### Major — Tentative discard choices are treated as submitted escrow

This is an adjudication-dependent deviation, not a contradiction of publisher text.

- Canonical decision ID: `CATAN-CLAR-DISCARD-ESCROW`
- Evidence type: `human_decision`
- Source: `CATAN-V2-SOURCE-GAP-CLARIFICATIONS`, JSON Pointer `/clarifications/1/decision`
- Exact evidence: “A submitted selection becomes private escrow … It … is unavailable to Monopoly, robbery, trade, building, maritime trade, or any other interrupt.”
- Conflicting code: `Game._available`, lines 146–151.
- Expected: Only a selection finalized through `submit_discard` enters escrow and becomes unavailable to an interrupting Monopoly.
- Implemented: `_available` subtracts every entry in `selected`, without checking `submitted_players`. Cards merely chosen tentatively are already protected.
- Impact: A player can tentatively select a resource before submission and incorrectly shelter it from an interrupting Monopoly.

### Minor — Played progress cards remain in `development_hand`

- Canonical fact ID: `CAT-C-PROGRESS-REMOVED`
- Evidence: `CATAN22-RULES`, PDF page 4: “Danach wird die Karte aus dem Spiel entfernt.”
- Conflicting code: `Game._play_dev`, lines 364–381.
- Expected: A played progress card leaves the game.
- Implemented: It is marked `revealed` inside `development_hand` and also copied into `bank.played_development`.
- Impact: It cannot be replayed and does not alter scoring, so this is chiefly a zone/inventory representation error.

## Rule-area coverage

| Rule area | Review result |
|---|---|
| Provenance and scope | Hashes match; beginner 3/4-player strict-phase scope respected |
| Illustrated setup and inventory | Covered; no contradiction found |
| Turn order and strict phases | Mostly correct; pre-roll development timing missing |
| Production and shortages | Covered, including robber blocking and all-or-none shortage decision |
| Seven, robber, and blind theft | Covered |
| Domestic and maritime trade | Covered; positive bilateral bundles and same-resource maritime prohibition respected |
| Building and piece stock | Covered except Longest Road recomputation after settlement |
| Development cards | Effects and one-per-turn limit covered; timing and played-progress zoning defects |
| Private information and observations | Generally covered; discard escrow boundary is wrong |
| Longest Road/Largest Army | Algorithms generally conform; settlement interruption transition is missing |
| Scoring and victory | Immediate active-player victory implemented, but stale Longest Road can corrupt it |
| Terminal returns | Consistent winner `+1`, others `-1`; no source conflict found |

## Deterministic scenarios needed

Without inspecting any existing scenario suite, these cases are necessary:

1. At `phase="roll"`, every eligible non-VP development type is available; a pre-roll Knight can immediately win via Largest Army.
2. An opponent settlement splits the current longest route:
   - one other player becomes uniquely longest;
   - incumbent remains part of a leading tie;
   - incumbent is excluded from a leading tie.
3. During seven-discard, a player tentatively chooses but does not submit a resource; interrupting Monopoly must still collect it.
4. Repeat with a submitted selection; its escrowed cards must remain protected and the exact pending discard must resume.
5. After playing Road Building, Year of Plenty, or Monopoly, the card is absent from the development-hand zone.
6. Regression: a positive five-card domestic exchange that gives four cards of a resource and receives one card of that same resource remains legal when both parties can pay.
7. A settlement interruption removes two Longest Road points before any later road action and before the affected player can win.

## Material questions for a human

None. All material findings are decided by either clear publisher text or the approved discard-escrow clarification. The meaning of `development_hand` as a true zone versus an audit-history collection could be confirmed, but it does not require rulebook clarification.

```text
score: 0.78
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```