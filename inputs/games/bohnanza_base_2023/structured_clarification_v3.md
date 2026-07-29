# Bohnanza Base Game 2023 — structured clarification and whole-game fidelity guide

## Provenance and use

This is a user-approved BoardBench experimenter supplement, not publisher text. Read it together with the unchanged publisher PDF. The PDF remains authoritative for every rule not explicitly clarified below. The checklist deliberately covers the whole game: do not optimize only one highlighted mechanic or treat an omitted PDF rule as optional.

Before finishing the implementation, trace every checklist item to concrete state, legal-action and transition logic. Check interactions at phase boundaries and game end, not only isolated helper functions.

## Clarified digital decisions

1. **Starting player:** use the supplied seed to select the starting player reproducibly. That player keeps the Start card for the whole game.
2. **Phase-three player order:** when several players have sideways staged cards, any affected player may plant next. Every affected owner chooses the order of their own cards. All staged cards must be planted before phase four.
3. **Anytime harvesting:** expose each player's source-legal harvest choices at stable decision boundaries, including off-turn boundaries. Do not interrupt one atomic draw, shuffle, transfer or planting transition.
4. **Private information:** a player sees their own complete ordered hand. For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.

## Balanced whole-game implementation checklist

### Setup and information

- Support exactly 3–5 players; reject player counts outside that range.
- Use the complete 104-card base deck: Garden 6, Red 8, Black-eyed 10, Soy 12, Green 14, Stink 16, Chili 18, Blue 20.
- Deal five ordered hand cards to every player. Three-player games give every player three fields; four- and five-player games give every player two fields.
- Preserve hand order: plant only from the front, never sort, and append later draws at the back in draw order.
- Each opponent's front card is public; deeper opponent cards remain private as clarified above.

### Four-phase turn

1. **Plant from hand:** the first front card is mandatory. The newly exposed front card is optional as a second planting. Never allow a third hand planting. An empty hand skips this phase. If a mandatory bean fits no field, require a separate legal harvest choice before planting; do not silently combine harvest and plant.
2. **Reveal and trade:** reveal two cards. The active player owns them initially. Every trade includes the active player; two non-active players cannot trade with each other. A proposed trade may contain any positive number of cards on either side, may be unequal, and may use arbitrary hand positions plus the active player's revealed cards. Neither hand changes before both participants consent. On acceptance transfer every referenced card atomically. Gifts also require recipient consent. Field cards and already received sideways cards cannot be traded. The active player explicitly ends trading.
3. **Plant staged cards:** every received sideways card and every active-player revealed card not traded away must be planted. Received cards never enter a hand. Follow the clarified inter-player and per-owner order above. A card that fits no field requires a separate harvest choice before planting continues.
4. **Draw:** the active player draws three cards sequentially and appends them unchanged to the back of the hand, then play advances clockwise.

### Fields and harvesting

- A field contains one bean type, but the same type may occupy multiple fields.
- Harvesting is legal at the stable boundaries clarified above, including off-turn harvesting.
- Singleton protection: a one-card field cannot be harvested while another field of the same player has more than one card; it may be harvested when none does.
- A legal harvest empties the field. The payout number of cards becomes coins and every other harvested card enters the discard pile. Zero-coin harvesting remains legal when singleton protection permits it.
- Implement every printed beanometer exactly:
  - Garden: size 1 → 0; 2 → 2; 3+ → 3.
  - Red: thresholds 2/3/4/5 pay 1/2/3/4.
  - Black-eyed: thresholds 2/4/5/6 pay 1/2/3/4.
  - Soy: thresholds 2/4/6/7 pay 1/2/3/4.
  - Green: thresholds 3/5/6/7 pay 1/2/3/4.
  - Stink: thresholds 3/5/7/8 pay 1/2/3/4.
  - Chili: thresholds 3/6/8/9 pay 1/2/3/4.
  - Blue: thresholds 4/6/8/10 pay 1/2/3/4.

### Depletion and game end

- On the first and second depletion, immediately shuffle the discard pile into a new face-down draw pile and continue the interrupted multi-card reveal or draw when cards are available.
- The third depletion ends the game immediately except during phase-two reveal. If it occurs during phase two, complete phases two and three, then end without phase four.
- At game end, harvest every field of every player before calculating results. Hand cards do not score. Each coin-pile card is one coin; highest total wins. Among tied leaders, the tied player farthest clockwise from the fixed Start-card holder wins.

## Final consistency audit

Verify setup for 3, 4 and 5 players; one complete normal turn; optional second planting; forced harvest as a separate decision; unrestricted positive trade-bundle sizes and consent; every owner's planting choices; off-turn harvest availability; all eight beanometers; first/second recycling during interrupted draws; third depletion inside and outside phase two; final harvest, coins and tie-break; and private observations/legal actions. This audit is source-derived guidance, not evaluator output.
