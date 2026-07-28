# Bohnanza Base Game 2023 V2 rule facts

- **status:** approved (2026-07-28)
- **condition:** publisher PDF only
- **source ID:** `BOHN-BASE-2023-RULES`
- **source role:** `publisher_rulebook`
- **source SHA-256:** `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`
- **scope:** complete supplied German base game, Version 5.4 / 2023, 3–5 players
- **atomic inventory:** `claims_v2.json`
- **approved decisions:** `decisions_v2.json`
- **scenario approval view:** `scenario_matrix_v2.md`

## Audit summary

The two complete publisher pages yield 92 atomic claims: 82 clear claims, 2 ambiguous claims, 7 missing claims and 1 untestable presentation claim. Of the clear claims, 81 are material and scored by the coverage register: 80 are scenario-mapped and `BOHN-C-HARVEST-ANYTIME` has one explicit non-exhaustive coverage exception, while deterministic off-turn and stable boundaries are tested. Exact shuffle order is clear but not deterministically scoreable because the source prescribes no permutation. Historical 157-card inventories, expansion beans, third-field purchasing, mutation conditions, prior clarification texts, old implementations and evaluator outputs are excluded.

## Clear rule groups

- exactly 104 cards in eight printed varieties: 6 Garden, 8 Red, 10 Black-eyed, 12 Soy, 14 Green, 16 Stink, 18 Chili and 20 Blue;
- 3–5 players, with three fields each at three players and two fields each at four or five, plus five dealt hand cards each;
- immutable hand order with a fully visible front card, mandatory front planting, optional second planting and no third hand planting;
- four ordered phases: hand planting; reveal/trade; planting received/revealed cards; sequential three-card draw and clockwise advance;
- bilateral active-player trades, arbitrary hand positions, revealed-card offers, unequal bundles, mutual consent, delayed atomic transfer, staged receipts, gifts and explicit trade ending;
- every owner plants all staged cards in their chosen own order, and the active player plants all untraded revealed cards;
- anytime own-field harvesting including off-turn permission, singleton protection, zero-value harvests, exact card-to-coin/discard conservation and all eight printed payout curves;
- first/second depletion recycle, third-depletion game end, the printed phase-two continuation exception, final harvest, ignored hands, one point per coin, highest-score winner and fixed-Start-card clockwise tiebreak.

## Approved human decisions

1. **Seeded start:** “Bestimmt, wer beginnt” is represented by a reproducible seed-selected start player.
2. **Phase-three inter-player order:** any affected owner with staged cards may plant next; all staged cards must finish before phase four, while each owner chooses their own card order.
3. **Anytime harvest boundary:** expose off-turn harvesting at stable player decision boundaries, not inside one atomic draw, shuffle, transfer or planting transition.
4. **Observation mapping:** expose the selected player's complete ordered hand and every opponent's size plus publisher-visible front card; hide only deeper opponent identities.

Immediate termination at third depletion outside phase two is classified publisher-clear: “sobald” states immediate end and the following sentence identifies phase two as the sole continuation exception.

## Visible but unscored gaps

- exact initial deal direction/grouping;
- empty or insufficient discard supply during a nonterminal recycle;
- stale numeric trade references after a pending proposal;
- simultaneous verbal negotiation priority;
- exact shuffle permutation;
- physical overlap, artwork and spoken announcements.

These remain missing or untestable claims rather than silent implementation rules. Snapshot card references and one pending proposal at a time will be documented as representation-only profile choices, not scored publisher rules.

## Coverage statement

The planned V2 matrix contains 42 cases: 38 clear-basis and 4 human-decision-basis. It maps 80 of 81 required clear claims and records one explicit clear coverage exception for exhaustive physical “anytime” timing. Player-count evidence will separately include exact setup, initial legal play and bounded reproducible play for 3, 4 and 5 players plus rejection of 2 and 6. Mapping coverage does not claim assertion completeness or total game correctness.
