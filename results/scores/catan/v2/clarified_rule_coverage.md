# Rule coverage

The implementation uses the illustrated beginner setup and strict phase sequence required by the representation profile. The approved digital clarifications are represented explicitly and are not treated as publisher rules.

| Source section / named rule | Implementing symbol | Probe or limitation | Assumption |
|---|---|---|---|
| Spielanleitung p.1–2, beginner preparation and illustrated setup | `SETUP`, `HEXES`, `HARBORS`, `Game.initial_state` | Initial-state serialization and fixture check | None |
| Turn overview; roll, trade, build | `legal_actions`, `apply_action` | Random rollout self-check | None |
| Resource production; settlement 1, city 2; shortage all-or-none | `_produce` | Source-only state probes through scripted rolls | None |
| Domestic trade | trade-offer actions, `_available` | Legal-action rollout; bounded builder per approved clarification | None |
| Maritime trade 4:1, 3:1, special 2:1 | `_ratio`, `maritime_trade` | Legal action requires bank stock and different receive resource | None |
| Road: brick + wood; connection and occupancy rules | `_legal_roads`, `build_road` | Every enumerated road action is applied in self-check | None |
| Settlement: brick + wood + wool + grain; distance rule | `_legal_settlements`, `build_settlement` | Every enumerated settlement action is applied | None |
| City: 3 ore + 2 grain; settlement upgrade | `build_city` | Every enumerated city action is applied | None |
| Development card: ore + wool + grain | `buy_development`, seeded deck | Seed determinism and rollouts | None |
| Knight / robber | `_play_dev`, `_push_robber`, robber phases | Scripted theft supported; mandatory victim choice per clarification | None |
| Road Building | `play_road_building`, `place_free_road` | Maximum feasible roads, up to two | None |
| Year of Plenty | `play_year_of_plenty` | Bank availability enforced | None |
| Monopoly | `play_monopoly` | Transfers available non-escrowed cards | None |
| Victory-point development cards | `_score`, `_victory` | Hidden until victory; minimum reveal in hand order | None |
| Seven: discard half, rounded down | discard actions and simultaneous settlement | Fixture and rollout checks; private escrow per clarification | None |
| Longest Road | `_road_length`, `_update_longest` | Edge-simple trail and opponent building interruption | None |
| Largest Army | `_update_army` | Three played knights minimum; transfer on strictly larger total | None |
| Game end at 10+ on own turn | `_victory`, `returns` | Checked after each committed action; terminal has no actions | None |
| Private resource and development information | `observation_to_data` | Opponent identities hidden; aggregate counts public | None |
| Variable setup / founding phase | Not implemented | Out of fixed beginner illustrated scope selected by profile | None |
| “Play it smart” app and product catalogue | Not game mechanics | Not probed | None |

Named costs: Road = wood+brick; Settlement = wood+brick+wool+grain; City = 3 ore+2 grain; Development = ore+wool+grain. Named development inventory: 14 Knights, two each Road Building/Year of Plenty/Monopoly, and one each Library/Marketplace/City Hall/Chapel/University.
