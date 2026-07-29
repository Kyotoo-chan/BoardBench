## Assessment

Score: **0.38**  
Confidence: **high**

The module implements much of the ordinary turn loop, card inventory, hand-order rule, harvest protection, most bean meters, recycling, serialization, and observation policy. However, final harvesting is entirely absent, so terminal scores and winners can be fundamentally wrong. There are also six material setup/action-rule deviations, including two rules specifically emphasized by the supplement.

## Findings

### Critical — Final fields are never harvested before scoring

- Canonical fact: `BOHN-C-FINAL-HARVEST`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person erntet noch ihre Bohnenfelder und erhält gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr. Anschließend zählen alle ihre Karten in ihrem jeweiligen Talerstapel.”
- Conflicting code: `_finish()` in [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:200)
- Expected: At game end, every field belonging to every player is harvested using its beanometer; those resulting coins determine the winner.
- Implemented: `_finish()` immediately compares existing `p["coins"]` and selects a winner. It neither scores nor empties any field.
- Impact: A player whose fields contain the winning final harvest can be declared the loser. This is a fundamentally wrong terminal/winner calculation. It also undermines `BOHN-C-HIGHEST-WINS`, because the compared totals omit required coins.

### Major — Three-player setup has one field too few per player

- Canonical fact: `BOHN-C-FIELDS-3`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1
- Exact evidence: “Spielt ihr zu dritt, legt ihr die Seite mit den drei Bohnenfeldern vor euch ab. Spielt ihr zu viert oder zu fünft, legt ihr die Seite mit den zwei Bohnenfeldern vor euch ab.”
- Conflicting code: `Game.initial_state()`, player construction at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:72)
- Expected: Three fields for every player when `num_players == 3`; two fields at four or five players.
- Implemented: Every player always receives `[[], []]`.
- Impact: The entire three-player legal planting and forced-harvest space is materially altered.

### Major — Garden Bean payouts are incorrect

- Canonical fact: `BOHN-C-PAYOUT-GARTEN`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1, Garden Bean beanometer
- Exact evidence: “[Visual transcription of the named card’s Bohnometer, page 1] Garden: size 1 pays 0, size 2 pays 2, size 3 or more pays 3.”
- Conflicting code: `METERS["gartenbohne"]` at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:12)
- Expected: `1 → 0`, `2 → 2`, `3+ → 3`.
- Implemented: `1 → 0`, `2 → 1`, `3+ → 2`.
- Impact: Every paying Garden Bean harvest is short by one coin and can change the winner.
- Provenance note: This is also explicitly repeated by `BOHN-EMPH-GARDEN-METER` at `/emphasis/1` in `BOHN-V2-CLEAR-RULE-EMPHASIS`.

### Major — Source-legal larger trade bundles are capped at two cards per side

- Canonical facts: `BOHN-C-TRADE-UNEQUAL`, `BOHN-C-TRADE-ANY-HAND-POSITION`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.” and “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting code: `_trade_proposals()` at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:153)
- Expected: A complete agreed bundle can include the available source-legal number of hand/revealed cards, with unequal cardinalities.
- Implemented: `offers` and `requests` contain only one- and two-card combinations. Three-or-more-card bundles cannot be proposed.
- Impact: Materially legal negotiated exchanges are absent.
- Provenance note: `BOHN-EMPH-UNEQUAL-MULTICARD-TRADE` at `/emphasis/0` requires complete atomic bundles and specifically warns against reducing source-legal multicard proposals.

### Major — Owners cannot choose the planting order of their staged cards

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `legal_actions()` and `apply_action()` at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:132)
- Expected: Each owner chooses any remaining received/revealed card to plant next.
- Implemented:
  - Only `cards[0]` is offered.
  - Plant actions always use `index=0`.
  - Received cards are forcibly exhausted before the active player may choose an untraded revealed card.
- Impact: Planting and forced-harvest outcomes can change based on an ordering the rule assigns to the player.

### Major — Off-turn harvesting is unavailable to most players at stable boundaries

- Canonical facts: `BOHN-C-HARVEST-OFFTURN`, `BOHN-C-HARVEST-ANYTIME`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht die aktive Person bist.”
- Conflicting code: `legal_actions()` at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:103)
- Expected: At stable decision boundaries, every player must be able to harvest their own eligible field, including while off turn.
- Implemented: Harvest actions are generated only for `current_player`. During most of an active player’s turn, other players cannot harvest; they receive occasional access only when independently selected as a trade respondent or phase-three planter.
- Impact: A material anytime action is broadly unavailable.
- Human-decision support: `canonical_rulefacts.md`, “Approved human decisions,” item 3 limits the digital implementation to stable boundaries but does not limit harvesting to the currently selected player.

### Major — Phase-three player order is fixed despite the approved choice policy

This is adjudication-dependent and separate from the printed-rule contradictions above.

- Canonical fact: `BOHN-M-PHASE3-INTERPLAYER-ORDER`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, `canonical_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “any affected owner with staged cards may plant next; all staged cards must finish before phase four, while each owner chooses their own card order.”
- Conflicting code: `_next_phase3_actor()` at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:210)
- Expected: Any affected owner may be selected to plant next.
- Implemented: The next owner is always the candidate with minimum clockwise distance from the active player.
- Impact: The approved phase-three action choice is removed, which can alter the timing of harvests and planting decisions.

### Question — Empty discard during a nonterminal recycle is silently treated as game end

- Canonical fact: `BOHN-M-EMPTY-DISCARD-RECYCLE`
- Source gap: `canonical_rulefacts.md`, “Visible but unscored gaps”
- Conflicting code: `_recycle_or_end()` at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-OhQ2Es/boardbench_bohnanza_base_2023_codex_ag_judge_1_b2c0smgt/implementation.py:183)
- Implemented assumption: After a first or second depletion, an empty discard causes `_finish()`.
- Question: What should the digital game do when a required nonterminal recycle has no cards? The approved packet explicitly leaves this undecided, so this is not scored as a contradiction.

### Question — Direction of a card-only gift

- Canonical fact: `BOHN-C-GIFT-CONSENT`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken.”
- Code: `_trade_proposals()` only constructs active-player-to-partner gifts.
- Question: Does the reciprocal wording require representing a partner-to-active gift, or must every digital proposal contain at least one card from the active player? The atomic claim records consent but does not expressly resolve gift direction.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Scope and inventory | Pass | 3–5 validation; 104 cards and all eight counts correct |
| Setup | Major defect | Five-card deal and seeded start present; three-player field count wrong |
| Hand information/order | Pass | Front planting, immutable order, append order, opponent-front observation represented |
| Phase-one planting | Pass | Mandatory first, optional second, no third, forced harvest available |
| Reveal/trade | Partial | Reveal, consent, staging, rejection and atomic transfer present; bundle cap limits legal trades |
| Phase-three planting | Major defects | All staged cards are forced, but owner order and approved inter-player choice are absent |
| Draw/advance/recycle | Mostly pass | Sequential three-card draw and clockwise advance; empty-discard case is unresolved |
| Harvesting | Major defects | Singleton protection and most meters correct; Garden meter and general off-turn access wrong |
| Third depletion | Pass in traced transitions | Phase-two exception and immediate outside-phase-two termination are represented |
| Final scoring/returns | Critical defect | Final harvest omitted; resulting winner and returns may be wrong |
| Serialization/observation | Mostly pass | Ordered own hand and visible opponent front align with approved observation mapping |

## Missing deterministic scenarios

- Three-player setup asserting exactly three fields per player, followed by legal use of the third field.
- Garden Bean harvests at sizes 1, 2, 3, and above 3.
- A third depletion where final field harvests change the leading player.
- A phase-two third depletion that completes phases two and three, performs final harvest, and never enters phase four.
- Three-for-one, one-for-three, and mixed hand/revealed atomic trades.
- Rejection of a multicard trade with both hands and revealed cards unchanged.
- A recipient choosing the second or later staged card before the first.
- The active player choosing between received and untraded revealed cards.
- Multiple affected phase-three owners choosing which owner plants next.
- Each non-active player harvesting at representative stable boundaries, including while neither respondent nor current phase-three planter.
- Final-harvest tie creation followed by the fixed-Start-card clockwise tiebreak.
- Empty-discard recycling behavior once a human policy is approved.
- Partner-to-active gift behavior once its direction is clarified.

## Material questions for a human

1. What is the required behavior when the first or second depletion requires recycling but the discard pile is empty?
2. Must the action model allow a non-active partner to give cards to the active player without receiving any card, or are gifts restricted to active-player-to-partner offers?

score: 0.38
confidence: high
critical_issues: 1
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true