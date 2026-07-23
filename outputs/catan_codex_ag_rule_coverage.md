# Rule coverage

The implementation models the fixed four-player beginner setup identified by the
representation profile. The optional “Play it smart” app mode, variable setup,
recommended merged trade/build variant, expansions, tactics, catalogue, and
publishing matter are source sections but are outside that configured game.

| Supplied section / named rule or card | Implementing symbol | Probe / exclusion / assumption |
|---|---|---|
| Rules overview; beginner setup; preparation | `Game.initial_state`, `HEXES`, `HARBORS`, `SETTLEMENTS`, `ROADS`, `START` | Initial payload probe; exact profile fixture round trip |
| Turn overview; resource roll | `legal_actions`, `apply_action`, `_produce` | Rollout probe; source-only production examples encoded by adjacency |
| Trade; domestic trade | `trade`, `trade_offer`, `_add_trade`, `_commit_trade` | Rollout probe; gifts rejected; only active-player bilateral legs |
| Maritime trade; harbor site | `_ratio`, `maritime_trade` | Legal-action probe for 4:1, 3:1, and 2:1; source-clear requirement that the received resource differ from the paid resource |
| Build; costs | `COSTS`, build branches in `legal_actions` and `apply_action` | Legal-action and atomic payment probe |
| Road; paths; coast | `_road_legal`, `_place_road`, `EDGE_VERTICES` | All canonical edges probed by rollouts/fixtures |
| Settlement; intersection; distance rule | `_settlement_legal`, `_place_settlement`, `ADJ` | Occupancy, road connection, and adjacent-building probe |
| City | `build_city` transition | Settlement replacement, piece return, cost, and score probe |
| Development cards | `buy_development`, `_dev_actions`, `_remove_dev` | Deck/private-hand and bought-this-turn restriction probe |
| Knight | `play_knight`, `_move_robber`, `_steal` | Before/after-roll phases and victim probe; A-03 |
| Progress: Road Building | `play_road_building`, `place_free_road`, `_finish_road_building` | Maximum feasible up to two, re-evaluated sequentially |
| Progress: Year of Plenty (“Erfindung”) | `play_year_of_plenty` | Ordered two-resource combinations constrained by bank |
| Progress: Monopoly | `play_monopoly` | Transfers all named cards from every opponent |
| Victory-point cards: Library, Marketplace, City Hall, Chapel, University | `VP_CARDS`, `_score`, `_victory` | Each named card represented; automatic minimum reveal has no separate public field in profile |
| Seven rolled | `_begin_seven`, `_advance_discard` | Floor-half threshold, private committed choices, joint application |
| Robber; desert | `_move_robber`, `_produce`, `_steal` | Must move to another hex; blocks production; eligible victim choice |
| Longest Road | `_road_length`, `_longest_road` | Edge-simple trail, opponent-building stop, tie retention/removal |
| Largest Army | `_largest_army` | Threshold three and strictly larger transfer |
| Victory points; end of game | `_score`, `_victory`, `returns`, `is_terminal` | Active player, immediate 10+, terminal no-actions probe |
| Variable setup; founding phase | Not active in fixed beginner profile | Source-only review; no evaluator action vocabulary for setup |
| Trade/build separation lifted | Not selected | Source calls it an optional recommended variant; profile explicitly requires strict phases |
| “Play it smart” pages 2–4 | Not implemented | Explicit optional external-app mode; runtime network/files forbidden |
| Almanac tactics, number tokens | Constants/topology only | Explanatory/non-operative source sections |
| Almanac game catalogue and expansions | Not implemented | Descriptive material for other products, not base-game rules |
| Components/material counts | Initial inventory and piece counts | 19 resources/type, 25 development cards, 15/5/4 pieces per player |

Material gaps are recorded in `assumptions.json`. No remembered or web rules
were used.
