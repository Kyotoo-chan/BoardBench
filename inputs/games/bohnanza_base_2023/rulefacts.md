# Bohnanza Base Game 2023 — cited rule facts

- **status:** approved (2026-07-19)
- **condition:** publisher PDF only
- **source ID:** `BOHN-BASE-RULES`
- **role:** `publisher_rulebook`
- **authorship:** AMIGO Spiel + Freizeit GmbH; Uwe Rosenberg; illustrations Björn Pertoft
- **edition marker:** Version 5.4 (2023 PDF metadata)
- **path:** `inputs/games/bohnanza_base_2023/game_rules.pdf`
- **SHA-256:** `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`
- **pages:** 2
- **excluded sources:** the prior 157-card component JSON, expanded rulebook, mutations, rulefacts, scenarios, implementations, and reviews

## Clear facts

### Components and setup

- **BASE-INV-01 (`clear`, p. 1):** “Es gibt 104 Karten mit acht verschiedenen Bohnensorten.” The illustrated inventory is exactly: 6 Gartenbohnen, 8 Rote Bohnen, 10 Augenbohnen, 12 Sojabohnen, 14 Brechbohnen, 16 Saubohnen, 18 Feuerbohnen, and 20 Blaue Bohnen. Sum: 104.
- **BASE-SETUP-01 (`clear`, p. 1):** “Spielt ihr zu dritt, legt ihr die Seite mit den drei Bohnenfeldern vor euch ab. Spielt ihr zu viert oder zu fünft, legt ihr die Seite mit den zwei Bohnenfeldern vor euch ab.”
- **BASE-SETUP-02 (`clear`, p. 1):** “Bestimmt, wer beginnt. Diese Person erhält eine der beiden Start-Karten.” The Start card remains with that player for the whole game.
- **BASE-SETUP-03 (`clear`, p. 1):** “Mischt alle Karten und teilt an alle jeweils fünf Handkarten aus.” Remaining cards form the draw pile.

### Hand order and phases

- **BASE-HAND-01 (`clear`, p. 1):** “Die Reihenfolge der Karten auf deiner Hand darfst du während des gesamten Spiels nicht ändern. … Du darfst die Karten nicht sortieren.” The first dealt card is the front card; later cards are appended behind it.
- **BASE-TURN-01 (`clear`, p. 1):** Turns proceed clockwise through four phases: plant from hand; reveal/trade; plant traded/revealed cards; draw cards.
- **BASE-PLANT-01 (`clear`, p. 1):** A field contains only one bean type; the same type may occupy multiple fields.
- **BASE-PLANT-02 (`clear`, p. 1):** “Du musst die vorderste Bohnenkarte … anbauen.” A second new front card is optional; a third hand card is forbidden.
- **BASE-PLANT-03 (`clear`, p. 1):** An empty hand at phase-one start skips directly to phase two.
- **BASE-PLANT-04 (`clear`, pp. 1–2):** A mandatory card that fits no field forces a harvest before planting.

### Reveal, trade, and gifts

- **BASE-TRADE-01 (`clear`, p. 1):** The active player reveals the top two draw-pile cards publicly; those cards initially belong to the active player.
- **BASE-TRADE-02 (`clear`, p. 2):** Only the active player may trade with others; non-active players may not trade with one another.
- **BASE-TRADE-03 (`clear`, p. 2):** Any hand position may be traded. The active player may also trade revealed cards. Unequal quantities are legal.
- **BASE-TRADE-04 (`clear`, p. 2):** Received cards and cards already planted on fields may not be traded.
- **BASE-TRADE-05 (`clear`, p. 2):** “Beide beteiligten Personen müssen dem Handel zustimmen.” Hand cards transfer only after both participants consent.
- **BASE-TRADE-06 (`clear`, p. 2):** Received cards are placed beside fields and never enter the hand.
- **BASE-TRADE-07 (`clear`, p. 2):** Gifts are a special trade and require recipient consent; rejection transfers nothing.
- **BASE-TRADE-08 (`clear`, p. 2):** The active player explicitly ends the optional trading phase.
- **BASE-PHASE3-01 (`clear`, p. 2):** Every player must plant all received cards; the active player must also plant every untraded revealed card. Each affected player chooses their own planting order.
- **BASE-DRAW-01 (`clear`, p. 2):** The active player draws three sequential cards, appends them in unchanged order, and the player to the left becomes active.

### Harvest and payouts

- **BASE-HARVEST-01 (`clear`, p. 2):** “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht die aktive Person bist.”
- **BASE-HARVEST-02 (`clear`, p. 2):** Payout follows the printed Bohnometer; paid cards become coins, all remaining field cards enter discard, and the harvested field becomes empty. Zero-coin harvests are legal.
- **BASE-HARVEST-03 (`clear`, p. 2):** A singleton field may not be harvested while another field of the same player contains more than one card.
- **BASE-PAY-01 (`clear`, pp. 1–2, graphical beanometers):** Minimum field sizes for 1/2/3/4 coins are: Garten `-/2/3/-`; Rot `2/3/4/5`; Augen `2/4/5/6`; Soja `2/4/6/7`; Brech `3/5/6/7`; Sau `3/5/7/8`; Feuer `3/6/8/9`; Blau `4/6/8/10`. A dash means that payout level is not printed. The Saubohne schedule is additionally stated in prose on p. 2.

### Recycling, ending, and scoring

- **BASE-END-01 (`clear`, p. 2):** Drawing the last card empties the draw pile; for the first two emptyings, shuffle discard into a new face-down draw pile.
- **BASE-END-02 (`clear`, p. 2):** “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- **BASE-END-03 (`clear`, p. 2):** If the third emptying occurs during phase-two reveal—even after only one revealed card—finish phases two and three, but not phase four.
- **BASE-SCORE-01 (`clear`, p. 2):** At game end every player harvests all fields; hand cards do not count; each coin-pile card is worth one coin.
- **BASE-SCORE-02 (`clear`, p. 2):** Highest coin count wins. Among tied players, the winner is the tied player farthest clockwise from the fixed Start-card holder.

## Not testable without adding source claims

- **BASE-INFO-01:** The PDF says the front card is completely visible in the holder's physical hand, but does not define a complete opponent-observation/privacy policy.
- Physical overlap, spoken announcements, overview-card possession, and artwork are presentation details rather than environment behavior.
- Exact initial deal direction/grouping, empty-discard behavior, and insufficient nonterminal recycle supply are not specified and will not receive hard expectations.

## Approved evaluator decisions (2026-07-19)

1. **D-BASE-END (`human_decision`):** Interpret “endet, sobald” as immediate termination when the third emptying occurs outside phase two. Do not recycle the discard and do not require remaining phase-four draws. The explicit phase-two continuation is the only exception. **Rationale:** this gives effect to the general immediate rule and its sole printed exception.
2. **D-BASE-OBS (`human_decision`, interface only):** Canonical player observations expose own hand identities/order and opponents' hand sizes, fields, coins, revealed cards, and other public state, but not opponents' hand identities/order. Privacy is not scored for rule fidelity. **Rationale:** avoid adding public access to unspecified opponent card identities.
3. **D-BASE-INTERRUPT (`human_decision`):** Represent “jederzeit” harvesting at every stable player decision boundary, including off-turn, but not as an interrupt inside one atomic draw, shuffle, transfer, or planting transition. **Rationale:** preserve off-turn harvesting without inventing sub-action interruption semantics.

## Explicit non-rule decision (2026-07-23)

- A proposed trade-fairness heuristic based on printed bean frequencies is **not** a gameplay rule and does not restrict legal trades or scored expectations. If a future example agent policy uses it, compare the sums of the printed frequencies on both sides and allow a maximum difference of six; this optional policy must remain outside the environment's legality rules.

## Proposed scenario changes

### Keep and recite for the base source

- Exact 104-card/eight-type inventory and 3/4/5-player setup.
- Immutable hand order, mandatory first/optional second/no third hand planting, empty-hand skip.
- Same-type field constraint and forced harvest.
- Reveal two; active-only bilateral trade; arbitrary hand positions; unequal exchange; mutual consent; rejected gifts; received-card staging; no onward trade.
- Mandatory phase-three planting with player-chosen order.
- Active player draws three and appends in order.
- Off-turn harvesting, singleton protection, zero-value harvest, full-field clearing, and all eight payout curves.
- First/second recycle, third-depletion phase-two continuation, final harvest, ignored hands, scoring, and tie-break.

### Remove entirely

- Ackerbohne, Weinbrandbohne, Kaffeebohne, and every associated count, payout, special ability, or purchasing test.
- The old 157-card catalogue expectation.
- Ackerbohne third-field purchase/unlock scenarios.
- The variant where every player draws one card clockwise.
- All mutated-source conditions and mutation-specific expectations from the active base workflow.
