# Rule coverage

The implementing symbols below are in `implementation.py`. Probes are source-only behavioral checks performed through public methods unless noted.

| Supplied section / named rule | Implementing symbol | Probe or reason not probed | Assumption |
|---|---|---|---|
| Spielidee / objective | `returns`, `_finish` | Terminal fixture returns only the winner | — |
| Spielmaterial & Spielvorbereitung / 104 cards, eight sorts | `BEANS`, `COUNTS`, `initial_state`, `state_from_data` | Fixture inventory counter covers every printed count | — |
| 3 players: three fields; 4–5: two | `initial_state` | Initial states constructed for 3, 4, 5 | — |
| Five hand cards; hand order may never change | `initial_state`, `apply_action` plant/draw | Initial hands length five; plant index is front; draw appends | — |
| Remaining cards become face-down deck; discard and coin piles | `initial_state`, `_draw_one`, `_do_harvest` | Inventory round-trip fixture | — |
| Start card retained; clockwise play | `initial_state`, draw transition | Seed repeatability and next-player arithmetic | A-01 |
| Four phases | `PHASES`, `legal_actions`, `apply_action` | Rollout traverses phase transitions | — |
| Fields contain one sort; same sort on several fields; rows overlap | `_fits`, plant transition | Legal plant actions inspect each field independently | — |
| Phase 1 mandatory front card | `legal_actions` (`plant_first`) | No pass with nonempty hand | — |
| Optional second front card; no third | `plant_second` actions and transitions | Pass and plant exposed; next phase is reveal | — |
| Forced harvest when no field fits; skip phase if hand empty | harvest actions, `pass` | Non-fitting card exposes harvest but no plant; empty-hand pass | — |
| Phase 2 reveal top two | `_draw_one`, reveal transition | Reveal action moves up to two deck-top cards in order | — |
| Only active player trades; others cannot trade together | `_validate_proposal`, trade actions | Actor and owner validation | — |
| Any hand position; revealed cards; unequal quantities | card references, `_validate_proposal`, `_remove_refs` | Arbitrary valid bundle accepted by transition; full exponential bundle set is not enumerated in `legal_actions` for tractability | A-02 |
| No field/already-received cards in trade | `_validate_proposal` | Zones restricted to hand/revealed | — |
| Consent before removing cards | trade-response state, accept transition | Reject leaves zones unchanged; accept transfers atomically | A-02 |
| Gifts require consent | gift proposals, trade response | Gift enters same accept/reject phase | A-02 |
| Acquired cards sideways; never enter hand | `zones.pending_received`, accept transition | Accepted cards enter recipient staging list | — |
| Active player decides when trading ends | `end_trade` | Only active player's end action | — |
| Phase 3 all traded and remaining revealed cards must be planted | `plant_received` actions | Draw/pass unavailable while staged cards exist | A-03 |
| Owner chooses planting order | staging lists and plant actions | Per-owner front staging card is chosen by its owner; received order records chosen order | A-03 |
| Phase 4 draw three, append without reordering | draw transition | Three sequential `_draw_one` calls append | — |
| Harvest at any time, including off-turn | harvest actions in every stable nonterminal state | Legal actions enumerate all players' fields | A-04 |
| Printed beanometers (all eight cards) | `METERS`, `_do_harvest` | Threshold table transcribed for Garden, Red, Black-eyed, Soy, Green, Stink, Chili, Blue | — |
| Harvest steps: count, consult top card, flip payout, discard rest, empty field | `_do_harvest` | Coin/discard/empty-field transition | — |
| Singleton protection | `_harvestable` | Singleton excluded if another field has 2+ | — |
| Empty deck: mix discard and continue | `_draw_one` | Profile recycle fixture reconstructs; transition uses deterministic shuffle | — |
| End after deck empties third time; phase-2 exception | `_draw_one`, reveal/plant-received/draw transitions | Third depletion in reveal defers; draw ends immediately | — |
| End: harvest all fields; hand ignored; one coin per card | `_finish` | Terminal cleanup invokes beanometers and compares coins | — |
| Tie: farthest clockwise from start card | `_finish` | Cyclic scan selects last tied player | — |
| Terminal states have no legal actions | `legal_actions` | Self-check assertion | — |
| Private ordered hands and visible opponent front card | `observation_to_data` | Privacy fixture verifies own hand and opponent front only | — |

## Explicit implementation limitation

The rulebook permits arbitrarily sized trade bundles. `apply_action` accepts and validates every such bundle. `legal_actions` explicitly enumerates every singleton trade/gift (the normal human decision vocabulary), but does not enumerate the exponential power set of all possible bundles. A caller can construct a larger canonical `trade_propose` action and it is accepted when source-legal.
