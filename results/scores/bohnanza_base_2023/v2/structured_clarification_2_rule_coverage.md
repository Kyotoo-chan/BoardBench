# Rule coverage

| Supplied section / named rule | Implementing symbol | Probe / evidence | Assumption |
|---|---|---|---|
| Spielidee; most coins wins | `_finish`, `returns` | terminal winner and returns | none |
| Spielmaterial & Spielvorbereitung; 104 cards and 3–5 players | `BEANS`, `COUNTS`, `initial_state` | fixture inventory and all supported counts | none |
| Three fields at 3 players; two at 4–5 | `initial_state` | profile fixture check | none |
| Five ordered hand cards; never sort; draws append | `initial_state`, `apply_action` | deal/plant/draw list order | none |
| Seeded random start card and shuffles | `_chance_rng`, `initial_state`, `_draw_one` | repeatable initial payload | none |
| Opponent front card public; deeper cards private | `observation_to_data` | privacy fixture | none |
| Spielablauf; clockwise turns and four phases | `apply_action`, `PHASES` | rollout phase transitions | none |
| First hand card mandatory; second optional; never third; empty hand skips | `legal_actions`, `apply_action` | `plant_first`, `plant_second`, `pass` | none |
| One bean type per field; same type may occupy multiple fields | `_plantable` | plant action field filtering | none |
| Separate harvest required if a card fits no field | `legal_actions`, `_harvest_actions` | no combined harvest/plant action | none |
| Phase 2 reveals two cards | `_draw_one`, `apply_action` (`reveal`) | atomic two-card transition | none |
| Only active player trades; arbitrary positive unequal bundles | `_refs`, `_nonempty_subsets`, `legal_actions` | all offered/requested subsets | none |
| Active hand and revealed cards tradable; field/staged cards excluded | `_refs`, `legal_actions` | source-zone construction | none |
| Consent, rejection, and gifts | `trade_propose`, `trade_accept`, `trade_reject` transitions | proposal leaves sources unchanged; acceptance is atomic | none |
| Received cards remain staged and cannot be retraded | `zones.pending_received`, trade reference construction | zone exclusion | none |
| Phase 3: every owner chooses order; affected owners may act next | `legal_actions` (`plant_received`) | actions for every staged index/owner | none |
| Remaining revealed cards must be planted | `legal_actions`, `apply_action` | draw withheld until staged zones empty | none |
| Phase 4 draws three behind the hand | `apply_action` (`draw`) | sequential append | none |
| Anytime harvest at stable boundaries, including off-turn | `_harvest_actions`, `legal_actions` | harvest actions for every player in every nonterminal phase | none |
| Die Bohnenschutzregel (singleton protection) | `_harvestable` | singleton filtered iff another field has 2+ | none |
| Legal harvest empties field; payout cards become coins; remainder discarded | `_harvest` | inventory-preserving transition | none |
| Garden meter 1→0, 2→2, 3+→3 | `METERS["gartenbohne"]` | threshold table | none |
| Red meter 2/3/4/5→1/2/3/4 | `METERS["rote_bohne"]` | threshold table | none |
| Black-eyed meter 2/4/5/6→1/2/3/4 | `METERS["augenbohne"]` | threshold table | none |
| Soy meter 2/4/6/7→1/2/3/4 | `METERS["sojabohne"]` | threshold table | none |
| Green meter 3/5/6/7→1/2/3/4 | `METERS["brechbohne"]` | threshold table | none |
| Stink meter 3/5/7/8→1/2/3/4 | `METERS["saubohne"]` | threshold table | none |
| Chili meter 3/6/8/9→1/2/3/4 | `METERS["feuerbohne"]` | threshold table | none |
| Blue meter 4/6/8/10→1/2/3/4 | `METERS["blaue_bohne"]` | threshold table | none |
| First/second depletion reshuffles discard and continues interrupted draw | `_draw_one` | recycle fixture and seeded continuation | none |
| Third depletion ends immediately except phase-2 completion through phase 3 | `_draw_one`, `apply_action` (`reveal`, `draw`, `pass`) | depletion marker controls phase-3 finish | none |
| End: harvest every field; hands ignored; coins score | `_finish` | terminal transition | none |
| Tie: tied leader farthest clockwise from fixed start player | `_finish` | modular-distance tiebreak | none |
| Terminal states have no legal actions | `legal_actions` | self-check terminal invariant | none |
| Canonical state/action/observation public contract | serialization methods | profile fixture and agentic self-check round trips | none |

No material rule gap remains after applying the supplied structured clarification; `assumptions.json` is therefore empty.
