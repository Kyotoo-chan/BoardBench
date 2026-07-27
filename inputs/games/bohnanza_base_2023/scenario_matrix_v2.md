# Bohnanza Base 2023 V2 scenario matrix

- Status: **pending user approval**
- Atomic claims: **92**
- Required clear claims: **81/81 mapped**
- Coverage exception: `BOHN-C-HARVEST-ANYTIME` is publisher-clear but not exhaustively testable; deterministic stable boundaries are covered by `BOHN-R27` without claiming every physical instant.
- Executable cases planned: **42** (38 clear, 4 human decision)

| ID | Basis | Claims | Exact expectation |
|---|---|---|---|
| `BOHN-R01-3p-inventory-setup` | clear | `BOHN-C-PLAYERS`, `BOHN-C-FIELDS-3`, `BOHN-C-DEAL-FIVE`, `BOHN-C-INV-TOTAL`, `BOHN-C-INV-TYPES`, `BOHN-C-INV-GARTEN`, `BOHN-C-INV-ROT`, `BOHN-C-INV-AUGEN`, `BOHN-C-INV-SOJA`, `BOHN-C-INV-BRECH`, `BOHN-C-INV-SAU`, `BOHN-C-INV-FEUER`, `BOHN-C-INV-BLAU`, `BOHN-C-SETUP-SHUFFLE`, `BOHN-C-SETUP-DRAW-PILE`, `BOHN-C-INITIAL-DECK-SIZES`, `BOHN-C-DRAW-PILE-HIDDEN` | **Three-player inventory and setup:** With seed 20260727: exact 104-card inventory, same-seed reproducible shuffled order, three fields, five-card hands, 89-card draw pile whose identities are absent from player observations, and an initial legal action. |
| `BOHN-R02-4p-setup` | clear | `BOHN-C-PLAYERS`, `BOHN-C-FIELDS-4-5`, `BOHN-C-DEAL-FIVE`, `BOHN-C-SETUP-SHUFFLE`, `BOHN-C-SETUP-DRAW-PILE`, `BOHN-C-INITIAL-DECK-SIZES`, `BOHN-C-DRAW-PILE-HIDDEN` | **Four-player setup:** With seed 20260727: same-seed reproducible shuffle, four players each with two fields and five cards, an 84-card hidden draw pile and an initial legal action. |
| `BOHN-R03-5p-setup` | clear | `BOHN-C-PLAYERS`, `BOHN-C-FIELDS-4-5`, `BOHN-C-DEAL-FIVE`, `BOHN-C-SETUP-SHUFFLE`, `BOHN-C-SETUP-DRAW-PILE`, `BOHN-C-INITIAL-DECK-SIZES`, `BOHN-C-DRAW-PILE-HIDDEN` | **Five-player setup:** With seed 20260727: same-seed reproducible shuffle, five players each with two fields and five cards, a 79-card hidden draw pile and an initial legal action. |
| `BOHN-R04-player-count-contract` | clear | `BOHN-C-PLAYERS` | **Player-count boundary:** With seed 20260727 and bound 100, repeatedly choose the lexicographically first canonical action name: 3, 4 and 5 each remain terminal or actionable without crash/deadlock; 2 and 6 raise ValueError. |
| `BOHN-R05-start-card-fixed` | clear | `BOHN-C-START-CARD-FIXED` | **Fixed Start card:** The initial Start-card holder remains fixed while turns advance. |
| `BOHN-R06-seeded-start` | human_decision | `BOHN-A-START-SELECTION` | **Seeded starting player:** The same seed reproducibly selects the same start player. |
| `BOHN-R07-opponent-front-visible` | clear | `BOHN-C-OBS-FRONT`, `BOHN-C-DRAW-PILE-HIDDEN` | **Visible opponent front:** Opponent observations expose the source-visible front card. |
| `BOHN-R08-deeper-hand-private` | human_decision | `BOHN-M-OBS-DEEPER-HAND` | **Deeper opponent cards hidden:** The selected player sees their complete ordered hand; opponents expose only size and front card, never deeper identities. |
| `BOHN-R09-front-plant-preserves-order` | clear | `BOHN-C-HAND-FRONT`, `BOHN-C-HAND-ORDER`, `BOHN-C-FIRST-PLANT-MANDATORY` | **Mandatory front plant:** Only the front card is plantable and removing it preserves suffix order. |
| `BOHN-R10-second-optional-no-third` | clear | `BOHN-C-SECOND-PLANT-OPTIONAL`, `BOHN-C-NO-THIRD-HAND-PLANT` | **Optional second, no third:** The second front card may be planted or skipped; no third hand plant is legal. |
| `BOHN-R11-empty-hand-skip` | clear | `BOHN-C-EMPTY-HAND-SKIP` | **Empty-hand phase skip:** An empty hand begins directly with reveal. |
| `BOHN-R12-field-types` | clear | `BOHN-C-FIELD-ONE-TYPE`, `BOHN-C-SAME-TYPE-MULTIPLE-FIELDS` | **Field type constraints:** Mixed types are illegal while one type may occupy multiple fields. |
| `BOHN-R13-forced-harvest` | clear | `BOHN-C-FORCED-HARVEST` | **Forced harvest before planting:** A mandatory unmatched front card remains pending until a legal field is harvested and then is planted. |
| `BOHN-R14-four-phase-turn` | clear | `BOHN-C-PHASES` | **Four phase order:** A deterministic trace visits the four phase boundaries in printed order. |
| `BOHN-R15-reveal-two-owned` | clear | `BOHN-C-REVEAL-TWO`, `BOHN-C-REVEALED-OWNED-ACTIVE` | **Reveal two:** Two known top cards become public and controlled by the active player. |
| `BOHN-R16-trade-legality` | clear | `BOHN-C-TRADE-ACTIVE-ONLY`, `BOHN-C-TRADE-NONACTIVE-BLOCKED`, `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-REVEALED`, `BOHN-C-TRADE-UNEQUAL`, `BOHN-C-NO-FIELD-TRADE` | **Trade legality matrix:** Only active-involving trades over legal hand/revealed zones are exposed; unequal bundles are legal. |
| `BOHN-R17-accepted-trade` | clear | `BOHN-C-TRADE-CONSENT`, `BOHN-C-TRADE-TRANSFER-ON-ACCEPT`, `BOHN-C-RECEIVED-STAGED`, `BOHN-C-RECEIVED-NOT-HAND` | **Accepted trade atomicity:** Proposal leaves zones unchanged; acceptance atomically stages exact bundles without changing hand order otherwise. |
| `BOHN-R18-rejected-trade` | clear | `BOHN-C-TRADE-CONSENT`, `BOHN-C-TRADE-TRANSFER-ON-ACCEPT` | **Rejected ordinary trade:** Rejection transfers nothing. |
| `BOHN-R19-gift-consent` | clear | `BOHN-C-GIFT-CONSENT` | **Gift consent:** Gift acceptance stages and rejection leaves the source unchanged. |
| `BOHN-R20-no-retrade` | clear | `BOHN-C-NO-RECEIVED-RETRADE`, `BOHN-C-NO-FIELD-TRADE` | **No onward or field trade:** Staged received and planted cards are absent from offer actions. |
| `BOHN-R21-end-trade` | clear | `BOHN-C-END-TRADE`, `BOHN-C-CONTINUE-AFTER-REVEALED-TRADE` | **Continue and end trade:** The active player may continue hand trades and explicitly end phase two. |
| `BOHN-R22-plant-all-owner-order` | clear | `BOHN-C-PLANT-ALL-RECEIVED`, `BOHN-C-PLANT-OWNER-ORDER`, `BOHN-C-PHASE3-FORCED-HARVEST` | **Plant all staged cards:** Each owner chooses their staged-card order, all cards are planted, and an unmatched mandatory staged card forces a legal harvest before continuing. |
| `BOHN-R23-phase3-any-player-order` | human_decision | `BOHN-M-PHASE3-INTERPLAYER-ORDER` | **Arbitrary affected-player order:** Either affected owner may plant next; phase four waits until all are finished. |
| `BOHN-R24-active-plants-revealed` | clear | `BOHN-C-PLANT-UNTRADED-REVEALED` | **Plant untraded revealed cards:** The active player plants every retained revealed card before drawing. |
| `BOHN-R25-draw-append-clockwise` | clear | `BOHN-C-DRAW-THREE`, `BOHN-C-DRAW-APPEND-ORDER`, `BOHN-C-HAND-APPEND`, `BOHN-C-CLOCKWISE`, `BOHN-C-NEXT-PLAYER` | **Draw three and advance:** Known top cards append in order and the next clockwise player becomes active. |
| `BOHN-R26-offturn-harvest` | clear | `BOHN-C-HARVEST-OFFTURN` | **Off-turn harvest permission:** A non-active player can harvest their own legal field. |
| `BOHN-R27-stable-harvest-boundaries` | human_decision | `BOHN-A-HARVEST-INTERRUPT` | **Stable-boundary harvest:** In fixed plant-first, trade and multi-owner phase-three fixtures, a legal off-turn harvest is available at each stable state; no extra interrupt action is inserted within one atomic draw, shuffle, accepted transfer or plant transition. |
| `BOHN-R28-singleton-boundaries` | clear | `BOHN-C-SINGLETON-BLOCKED`, `BOHN-C-SINGLETON-ALLOWED` | **Singleton protection:** A singleton is blocked only while another own field has more than one card. |
| `BOHN-R29-zero-normal-harvest` | clear | `BOHN-C-HARVEST-BEANOMETER`, `BOHN-C-HARVEST-COIN-CARDS`, `BOHN-C-HARVEST-DISCARD-REST`, `BOHN-C-HARVEST-EMPTIES`, `BOHN-C-HARVEST-ZERO` | **Harvest conservation:** Zero and paying harvests empty fields, create exact coins and discard the rest. |
| `BOHN-R30-garten-curve` | clear | `BOHN-C-PAYOUT-GARTEN` | **Garten payout curve:** sizes 1/2/3/4/5/6 pay 0/2/3/3/3/3. |
| `BOHN-R31-rot-curve` | clear | `BOHN-C-PAYOUT-ROT` | **Rot payout curve:** sizes 1/2/3/4/5/6/7/8 pay 0/1/2/3/4/4/4/4. |
| `BOHN-R32-augen-curve` | clear | `BOHN-C-PAYOUT-AUGEN` | **Augen payout curve:** sizes 1/2/3/4/5/6/7/8/9/10 pay 0/1/1/2/3/4/4/4/4/4. |
| `BOHN-R33-soja-curve` | clear | `BOHN-C-PAYOUT-SOJA` | **Soja payout curve:** sizes 1–12 pay 0,1,1,2,2,3,4 from thresholds 2/4/6/7 and plateau thereafter. |
| `BOHN-R34-brech-curve` | clear | `BOHN-C-PAYOUT-BRECH` | **Brech payout curve:** sizes 1–14 use thresholds 3/5/6/7 and plateau at 4. |
| `BOHN-R35-sau-curve` | clear | `BOHN-C-PAYOUT-SAU` | **Sau payout curve:** sizes 1–16 use thresholds 3/5/7/8 and plateau at 4. |
| `BOHN-R36-feuer-curve` | clear | `BOHN-C-PAYOUT-FEUER` | **Feuer payout curve:** sizes 1–18 use thresholds 3/6/8/9 and plateau at 4. |
| `BOHN-R37-blau-curve` | clear | `BOHN-C-PAYOUT-BLAU` | **Blau payout curve:** sizes 1–20 use thresholds 4/6/8/10 and plateau at 4. |
| `BOHN-R38-first-recycle-reveal` | clear | `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-RECYCLE-CONTINUES-DRAW` | **First recycle during reveal:** Seed 20260727; deck top [blau], discard [feuer, soja, rot], depletions 0: reveal blau, increment to 1, empty discard into a seeded refill, reveal exactly one refill card, leave two deck cards, conserve the four-card multiset and remain nonterminal. |
| `BOHN-R39-second-recycle-draw` | clear | `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-RECYCLE-CONTINUES-DRAW` | **Second recycle during draw:** Seed 20260727; existing hand [garten], deck top [blau], discard [feuer, soja, rot], depletions 1: append blau plus exactly two refill cards, increment to 2, leave one deck card, empty discard, conserve order/multiset, and advance clockwise. |
| `BOHN-R40-third-depletion-phase2` | clear | `BOHN-C-END-THIRD`, `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-FINAL-HARVEST`, `BOHN-C-COIN-VALUE` | **Third depletion in phase two:** On depletions 2→3 during reveal, expose available card(s), finish trade and every mandatory phase-three planting, perform final harvest, skip phase four and terminate. |
| `BOHN-R41-third-depletion-outside-phase2` | clear | `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`, `BOHN-C-END-THIRD`, `BOHN-C-FINAL-HARVEST` | **Immediate third depletion:** When an exact phase-four draw empties the pile for the third time, stop before any remaining draw or next turn, final-harvest and terminate. |
| `BOHN-R42-final-score-tiebreak` | clear | `BOHN-C-FINAL-HARVEST`, `BOHN-C-FINAL-HANDS-IGNORED`, `BOHN-C-COIN-VALUE`, `BOHN-C-HIGHEST-WINS`, `BOHN-C-TIEBREAK`, `BOHN-C-START-CARD-FIXED` | **Final score and tiebreak:** Final fields score, hands do not, and farthest-clockwise tied leader wins. |

## Approved human decisions

1. The supplied seed reproducibly selects the start player.
2. During phase three, any affected owner may plant next; every staged card must be planted before phase four.
3. Off-turn harvest actions exist at stable decision boundaries, not inside atomic transitions.
4. Observations show own full hand and each opponent’s size and source-visible front card, but hide deeper opponent identities.

The immediate third-depletion behavior outside phase two is classified clear: “sobald” plus the explicit phase-two exception supports it directly.

## Deliberately unscored source gaps

Exact deal grouping/direction; empty or insufficient discard on nonterminal recycle; stale numeric trade references; simultaneous negotiation priority; exact shuffle permutation; physical overlap, artwork and spoken announcements.
