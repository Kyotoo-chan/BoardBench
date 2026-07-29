# Rule coverage

The implementation uses only the supplied German 2022 rule sheet and almanac. Evaluator topology and payload vocabulary come from `GAME_PROFILE.json`.

| Source section / named rule | Implementing symbol | Probe or unresolved reason | Assumption |
|---|---|---|---|
| Beginner setup; material; fixed board; initial resources | `Game.initial_state`, `SETUPS`, `HEXES`, `HARBORS` | `initial_state` canonical payload and 3/4-player fixture round trips | none |
| Turn overview: roll, trade, build | `legal_actions`, `apply_action` | random rollout traverses phases | A-01 |
| Resource production; settlement 1, city 2; robber blocks; shortages | `apply_action(roll_dice)` | scripted-roll fixture supported; all-or-none bank shortage | none |
| Seven: discard half (rounded down), move robber, steal | discard/robber pending frames; `_next_discard`, `_push_robber` | fixture frames and legal-action acceptance | none |
| Domestic trade; only active player trades | trade-offer actions and pending frame | rollout/action round trip | none |
| Maritime trade 4:1, 3:1, specialized 2:1 | `legal_actions(trade)`, `apply_action(maritime_trade)` | source-derived harbor ratios | none |
| Road: wood + brick; connected placement | `COST`, `_road_actions`, `_connected_edge` | legal actions are accepted | none |
| Settlement: wood + brick + wool + grain; road and distance rule | `_settlement_actions`, build transition | legal actions are accepted | none |
| City: 3 ore + 2 grain; settlement upgrade; double yield | city actions and production transition | legal actions are accepted | none |
| Development purchase: ore + wool + grain; hidden hand | `buy_development`, shuffled deck, observation sanitizer | seeded deck and observation payload | none |
| One development card per turn; not bought this turn; playable before roll | `_dev_actions`, `_play_card` | rollout/action round trip | none |
| Knight; robber; played knights | `play_knight`, robber pending frames | fixture nested interrupt supported | none |
| Largest Army: first 3, transfer on strictly more | `play_knight` transition | source-only state probe through fixtures | none |
| Road Building: two free legal roads | road-building frame, `place_free_road` | fixture frame and legal-action acceptance | none |
| Year of Plenty | `play_year_of_plenty` | legal pairs limited by bank availability | none |
| Monopoly | `play_monopoly` | transfers named resource from every opponent | none |
| Progress cards removed after use | revealed hand plus `bank.played_development` | canonical observation exposes played cards | none |
| Five named victory-point cards; hidden until win | `VP`, `_score`, `_victory` | observations omit hidden points | A-02 |
| Settlement 1 point; city 2; special cards 2; win at 10 on own turn | `_score`, `_victory`, `returns` | terminal fixture and rollout | A-02 |
| Longest Road; interruption by opponent building | state fields retained; no automatic award | not probed: incomplete general branching algorithm in source | A-03 |
| Variable setup / founding phase / tactics | not implemented | profile fixes illustrated beginner setup; not an active-game rule in this representation | none |
| Play it smart app and product catalogue | not implemented | optional external companion/product information, not base-game mechanics | none |

Action serialization is implemented by `action_to_data`/`action_from_data` and state/private observation serialization by `state_to_data`, `state_from_data`, and `observation_to_data`.
