# CATAN 2022 V2 rule facts

- **status:** frozen (2026-07-29) for V2 Original packet; no generation or evaluation has run
- **condition:** matching official 2022 German Spielanleitung plus CATAN-Almanach
- **scope:** illustrated beginner setup, 3 and 4 players, strict roll → trade → build
- **sources:** `CATAN22-RULES`, `CATAN22-ALMANAC`; see `source_register_v2.md`
- **atomic inventory:** `claims_v2.json`
- **approved digital decisions:** `decisions_v2.json`
- **scenario approval view:** `scenario_matrix_v2.md`

## Fresh audit summary

The complete 4-page primary and matching 24-page companion were read from the supplied PDFs and fresh 150-DPI page renders without web or remembered rules. After Original evaluation and pre-intervention gap approval, the inventory contains **125 claims**: **104 clear**, **2 ambiguous**, **17 missing**, **1 conflicting**, and **1 untestable**. Of the clear claims, **99** are material and executable; five physical accessory counts remain visible but are not represented as game state. All 99 required clear claims remain mapped into the hard matrix.

No in-scope cross-source conflict was found. The Almanac's combined trade/build procedure is an expressly recommended experienced-player option and is outside the approved beginner scope rather than a precedence conflict.

## Clear rule groups

The atomic register covers exact components; 3-player red removal and 4-player beginner setup; lettered starting resources; bank/development setup; clockwise strict phases; production and robber blocking; domestic and maritime trade; costs, stock, graph legality and city replacement; Longest Road and tie handling; seven/discards/robber; every development-card effect and Largest Army; source-visible privacy; scoring and immediate active-player victory.

## Approved decisions

1. **Scope:** illustrated beginner setup for both 3 and 4 players; strict phases; variable setup and experienced phase merge excluded.
2. **Shortages:** production of one resource is all-or-none across all entitlements; bank actions require their complete effect to be available; development purchase requires a card; Road Building places the maximum feasible number up to two.
3. **Longest Road:** maximum edge-simple trail; no edge reuse, vertex revisit allowed when the trail permits it, opponent vertices stop traversal.
4. **Chance/privacy:** constructor seed controls dice, deck and uniform blind theft; no eligible victim means no transfer; seven discards are private and simultaneous; public aggregate counts remain visible while identities stay private.
5. **Domestic trade:** finite bilateral offer builder, one partner, positive bundles on both sides, explicit accept/reject, atomic transfer only on acceptance.
6. **Victory cards:** reveal only the minimum number needed to establish ten, in development-hand order.
7. **Development interrupts:** subject to the clear one-card-per-turn limit, an eligible card may interrupt pending discard, seven-sourced robber or trade-consent decisions; resolve it on a pending-state stack, then resume unless terminal. A pending development-card effect cannot be interrupted by a second card.
8. **Immediate victory:** check after each committed atomic action or subaction; reaching ten immediately cancels any unfinished card effect.
9. **Finite trade bound:** give/take totals are capped by each side's public resource-hand size without revealing identities; acceptance validates actual holdings.
10. **Discard escrow:** submitted private selections are unavailable to interrupts and settle together after every required submission.
11. **Knight robbery:** with any adjacent opponent, a victim choice is mandatory; an empty adjacent hand remains selectable and transfers nothing.
12. **Maritime receive type:** 4:1, 3:1 and 2:1 exchanges must receive a type different from the type given.

An image-level reread of Almanac p.6 found the explicit text “Es gibt je zweimal” for Road Building, Year of Plenty and Monopoly. Their two-each distribution is therefore publisher-clear; the user's earlier answer to leave the distribution unknown is not applied because that question was based on an incomplete extracted-text premise.

## Visible source gaps

Publisher text does not define resource-bank shortages, unavailable bank actions, empty development deck, Road Building with fewer than two placements, software RNG, empty/no-adjacent robbery outcomes, digital discard protocol, finite trade consent protocol, public aggregate-count fields, digital development-card interrupt stacking, active-seat input, exact victory-card disclosure, or unfinished card effects at immediate victory. Complex Longest Road loop semantics are linguistically ambiguous. These remain non-clear claims and are scored only under the separately approved human-decision basis.

Spoken negotiation remains untestable. Random distribution quality beyond reproducibility and transfer invariants is not claimed as publisher correctness.

## Coverage statement

The intervention-comparison rubric r3 has **55 scenarios**: **40 clear-basis** and **15 human-decision-basis**. Numeric stems now extend through `R47`; letter-suffixed splits `R01A`–`R01C`, `R02A`–`R02C`, and `R04A`–`R04D` make the physical total 55 without renumbering prior stable IDs. It maps all 99 required clear claims without a coverage exception. Large setup/inventory bundles are split into explicit board, resource, development, piece, starting-resource, bank/deck and initial-action assertions. Mapping does not prove every clause is exhaustively asserted; setup, both approved player counts, initial legal play, bounded playability, and rejection outside 3–4 receive separate evidence.
