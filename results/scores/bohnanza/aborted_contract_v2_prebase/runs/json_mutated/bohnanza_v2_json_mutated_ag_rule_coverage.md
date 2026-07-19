# Rule coverage — Variant 2, Ackerbohnen (4–5 players)

Only `game_rules.pdf` supplies gameplay rules. `game_components.json` supplies observed identities, counts, and Bohnometer values.

| Source section / named rule | Implementation symbol | Probe / assumption |
|---|---|---|
| Grundspiel: material and preparation (p.3–4) | `BEANS`, `COUNTS`, `initial_state` | 4/5 players, two fields, five singly dealt ordered cards, shuffled deck; Variant 2 replaces the material selection as stated on p.10. |
| Hand order may never change (p.4) | `initial_state`, `legal_actions`, `apply_action` | Only hand index 0 can be planted; draws append. `reorder_hand` is intentionally never legal. |
| Draw/discard piles and public/private layout (p.4) | `zones`, `observation_to_data` | Opponent hands expose sizes only; fields, coins and revealed cards are public. |
| Turn order/start-player card (p.5) | `active_player`, `start_player`, draw transition | Clockwise successor; start player remains fixed. |
| Four phases (p.5) | `legal_actions`, `apply_action` phase branches | Explicit plant, reveal/trade, plant-received, draw states. |
| Planting: first mandatory, second optional; max one bean per field; same bean can occupy several fields (p.5) | `_plant_options`, `plant_first`, `plant_second` | Legal-action generation probes empty/same-bean fields and pass only after first planting. |
| Must harvest before planting if no fitting field; empty hand skips phase 1 (p.6, p.8) | `_plant_options`, `pass` | Harvest actions replace planting until space exists; empty hand exposes pass. |
| Reveal top two and trade (p.6) | `reveal`, `trade` | Draws two into `zones.revealed`; terminal depletion can interrupt. |
| Trade only active player with others; others not among themselves; hand position irrelevant; revealed cards tradeable (p.6) | `legal_actions` in `trade` | Only active actor creates proposals, against every other player's whole hand. |
| Received cards cannot be retraded or put in hand; field cards cannot be traded; unequal trades allowed (p.6) | `pending_received`, proposal generation | Received/field zones excluded. `trade_add_offer_card` / `trade_add_request_card` support arbitrary unequal multi-card proposals; gifts support zero-for-one. |
| Consent required; do not remove hand card until agreement (p.7) | `trade_response`, accept/reject branches | Proposal stores references; removal happens only on accept. |
| Gifts require consent (p.7) | `gift_propose`, `gift_accept`, `gift_reject` | Direct source probe via response actions. |
| Active may continue hand trading after revealed cards handled; active chooses phase end (p.7) | `trade`, `end_trade` | Accepted/rejected deals return to trade; explicit end action. |
| All traded/revealed cards must be planted; each player chooses order (p.8) | `plant_received` | Each recipient plants received cards. Proposal additions determine the order within each side of a multi-card deal. |
| Draw three in base game (p.8) | superseded by Variant-1 draw rule on p.10 | Not implemented for assigned condition. |
| Harvest any time, Bohnometer, cards as coins, remainder discard, field empty (pp.8–9) | `_harvest`, `PAY` | Harvest legal when needed for planting; voluntary anytime harvesting is not separately surfaced outside that need (see unresolved scope below). |
| Bean-protection rule: singleton cannot be harvested while any field has >1 (p.9) | `_harvestable` | Direct field-size predicate. |
| Empty deck: shuffle discard into new draw pile (p.10) | `_refill` | Deterministic seeded reshuffle. |
| Base game end, final harvest, hands do not count, most coins, clockwise tie from start player (p.10) | `_refill`, `returns` | Assigned condition uses third depletion via Variant 1; returns rank the specified tie winner. Final fields are deliberately not auto-harvested because p.10 states players harvest them; terminal interface cannot expose actions, a source/interface gap covered by A-01's omitted Variant-1 context. |
| Variant 1 visible tail: everyone draws one starting with active; 4+ ends on third empty deck (p.10) | `draw`, `_refill` | Direct assigned Variant-2 reference to Variant 1. |
| Variant 2 material: base beans + Ackerbohne + Weinbrandbohne; 4–5; two fields (p.10) | `BEANS`, `COUNTS`, constructor | Kaffeebohne and Kakaobohne excluded; exact 129-card deck. |
| Variant 2 otherwise follows Variant 1 (p.10) | full phase machine | Omitted Variant-1 pages recorded as A-01. |
| Ackerbohne harvest: 2 cards → 2 coins and third returned to field back; 3 cards → 3 coins; singleton gives nothing (p.11) | `_harvest` | With exactly three cards in the deck, ordinary removal produces the same 2/3 outcomes. Rare reconstructed surplus states are handled conservatively. |
| Blaue Bohne 20 (4/6/8/10 → 1/2/3/4) | `COUNTS`, `PAY` | Component observation. |
| Feuerbohne 18 (3/6/8/9 → 1/2/3/4) | `COUNTS`, `PAY` | Component observation. |
| Saubohne 16 (3/5/7/8 → 1/2/3/4) | `COUNTS`, `PAY` | Component observation. |
| Brechbohne 14 (3/5/6/7 → 1/2/3/4) | `COUNTS`, `PAY` | Component observation. |
| Sojabohne 12 (2/4/6/7 → 1/2/3/4) | `COUNTS`, `PAY` | Component observation. |
| Augenbohne 10 (2/4/5/6 → 1/2/3/4) | `COUNTS`, `PAY` | Component observation. |
| Rote Bohne 8 (2/3/4/5 → 1/2/3/4) | `COUNTS`, `PAY` | Component observation. |
| Gartenbohne 6 (2/3 → 2/3) | `COUNTS`, `PAY` | Component observation. |
| Weinbrandbohne 22 (2/4/6/8 → 1/2/3/4) | `COUNTS`, `PAY` | Included by Variant 2; component observation. |
| Ackerbohne 3 (2/3 → 2/3) | `COUNTS`, `_harvest` | Rulebook p.11 and component observation agree. |
| Kaffeebohne 24, Kakaobohne 4 | excluded from `BEANS` | Supplied component names audited but Variant 2 expressly excludes them. |

Unresolved implementation boundary: the source permits harvesting “at any time.” A turn-based API needs an actor/continuation convention not specified by the rulebook. The implementation exposes every harvest required to make a pending planting legal, while all scoring logic supports every named bean. This is a known incompleteness rather than an invented timing rule.
