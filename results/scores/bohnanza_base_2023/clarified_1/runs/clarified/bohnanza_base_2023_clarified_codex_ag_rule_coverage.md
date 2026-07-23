# Rule coverage

Only the two supplied publisher pages and the four assigned clarifications are used as behavioral evidence. `ENVIRONMENT_CONTRACT.md` and `GAME_PROFILE.json` are used only for representation.

| Source section or named rule | Implementing symbol(s) | Source-only probe / status | Assumption |
|---|---|---|---|
| Spielidee: plant, trade, harvest; most coins wins | `Game.legal_actions`, `Game.apply_action`, `Game.returns` | Rollout and terminal probes pass | A-01 affects ties/start |
| Spielmaterial & Spielvorbereitung: 3–5 people | `Game.__init__` | Constructors reject outside 3–5; fixture checks 5 | None |
| Three fields for 3 people; two for 4–5 | `Game.initial_state` | Fixture inspection verifies 3/2 | None |
| Start-Karte remains with starter | `start_player`, `active_player` | State round-trip preserves both | A-01 |
| 104 cards and eight bean types | `BEANS`, `COUNTS`, `Game.initial_state` | Inventory probe verifies 104 and 6/8/10/12/14/16/18/20 | None |
| Gartenbohne (6) | `COUNTS`, `THRESHOLDS` | Count and 2→2, 3+→3 payout probes | None; payout text from CLAR-PAY-01 |
| Rote Bohne (8) | `COUNTS`, `THRESHOLDS` | Count and 2/3/4/5 payout probes | None |
| Augenbohne (10) | `COUNTS`, `THRESHOLDS` | Count and 2/4/5/6 payout probes | None |
| Sojabohne (12) | `COUNTS`, `THRESHOLDS` | Count and 2/4/6/7 payout probes | None |
| Brechbohne (14) | `COUNTS`, `THRESHOLDS` | Count and 3/5/6/7 payout probes | None |
| Saubohne (16) | `COUNTS`, `THRESHOLDS` | Count and 3/5/7/8 payout probes | None |
| Feuerbohne (18) | `COUNTS`, `THRESHOLDS` | Count and 3/6/8/9 payout probes | None |
| Blaue Bohne (20) | `COUNTS`, `THRESHOLDS` | Count and 4/6/8/10 payout probes | None |
| Shuffle and deal five hand cards | `Game.initial_state` | Inventory, hand-size, and equal-seed probes | A-02 |
| Hand order may never change; first dealt is front; no sorting | list order; `_plant_actions` restricts hand source to index 0; draw appends | Plant/draw and round-trip probes preserve order | A-02 only for deal cadence |
| Remaining cards form draw pile; discard and coin piles arise in play | `zones.deck`, `zones.discard`, `players[].coins` | Harvest and recycle probes | Coin cards are represented by the coin integer and leave card zones, as required by the profile |
| Spielablauf: clockwise active person; Start-Karte not passed | draw transition; `start_player` | Turn-advance probe | A-01 |
| Four phases | phase state machine in `legal_actions` / `apply_action` | Agentic rollout visits phase transitions | None |
| Phase 1: mandatory front card | `_plant_actions`, `plant_first` | Legal-action probe permits only hand index 0 | None |
| Phase 1: optional second front card; third forbidden | `plant_second`, `pass` | Transition probe | None |
| Same type per field; same type may occupy several fields; cards overlap | `_plant_actions`, `_validate_state`, plant append | Compatible/incompatible-field probes | None |
| If mandatory bean has no suitable field, harvest first | separate always-available `harvest`, no incompatible `plant` | Legal-action probe | None |
| Empty hand at start of phase 1 skips to phase 2 | `pass` in `plant_first` only when hand empty | Empty-hand probe | None |
| Phase 2: reveal top two cards | `reveal`, `_draw_one` | Reveal probe | A-04 at third depletion |
| Revealed cards belong to active person and are available for planting/trading | `zones.revealed`, `_trade_actions`, `plant_received` | Trade/plant probes | None |
| Only active person trades; other people may not trade among themselves | `_trade_actions`, proposal actor validation through legal membership | Actor probe | A-03 for proposal protocol |
| Any own hand card may be traded regardless of hand position | `_trade_actions` hand references | Subset probe includes non-front indices | None |
| Active person may trade the two revealed cards | `_trade_actions` revealed references | Offered-pool probe | None |
| Received cards, field cards, and cards received in the same trade phase may not be retraded | pools omit `pending_received` and fields | Legal-action probe | None |
| Unequal quantities; no 2-for-1 cap (CLAR-TRADE-01) | `_nonempty_subsets`, `_trade_actions` | Probe includes 1-for-2 and 3-for-1 | None |
| Both parties must consent; card stays in hand until deal exists | `trade_response`, `trade_accept`, `trade_reject`, `pending` | Accept/reject transition probes | A-03 |
| Obtained cards lie beside fields and may not enter hand | `zones.pending_received` | Accept probe | None |
| Gifts require recipient consent | `gift` proposals and same response phase | Gift accept/reject probe | A-03 |
| Active person may continue trading and ends the phase | return to `trade`; `end_trade` | Transition probe | None |
| Phase 3: every recipient plants all obtained cards, in chosen order (CLAR-PHASE3-01) | `plant_received`, `_next_received_player`, arbitrary received index | Multi-player fixture/transition probe | None |
| Active person also plants untraded revealed cards | `plant_received` revealed source | Transition probe | None |
| Incompatible required card forces harvest before planting | no incompatible plant plus always-available harvest | Legal-action probe | None |
| Phase 4: active person draws three in unchanged order behind hand | `draw`, three `_draw_one` calls, append | Draw-order probe | None |
| Next person clockwise becomes active | draw transition | Turn-advance probe | None |
| Die Bohnenernte: harvest at any time, even off turn | `_harvest_actions` for every player in every nonterminal phase | Off-turn action probe | None |
| Beanometer payout; some harvests pay zero | `THRESHOLDS`, `_coins_for`, `_apply_harvest` | All threshold/below-threshold probes | CLAR-PAY-01 supplies transcription |
| Turn paid cards to coin side; discard unpaid cards; field becomes empty | `_apply_harvest` | Harvest transition probe | None |
| Bohnenschutzregel: no singleton harvest if another own field has >1 card | `_can_harvest` | Protected/unprotected probes | None |
| Ein leerer Nachziehstapel: shuffle discard into new draw pile | `_empty_deck` | Seeded recycle probe | None |
| Third depletion ends game; phase-2 exception (CLAR-END-01) | `_empty_deck`, `_next_received_player` | Draw immediate-terminal and reveal/deferred-terminal probes | A-04 |
| At end, harvest all fields; hand is worthless; highest coin total wins | `returns` adds field beanometer values and ignores hands | Terminal scoring probe | None |
| Tie: farthest clockwise from Start-Karte wins | `returns` modular distance | Tie probe | A-01 fixes the initial Start-Karte holder |
| Terminal states have no actions | `legal_actions` terminal guard | Agentic self-check | None |
| Seed controls all chance | initial shuffle and recycle shuffle derived from `seed` and `draw_index` | Equal-seed state/successor probes | None |
| Private hands and public fields/reveals/counts | `observation_to_data` | Contract round-trip/detachment probes | The source does not define a formal observation payload; profile fields constrain representation only |

## Validation probes

`python agentic_self_check.py` exercises canonical state/action/observation round trips, legal-action acceptance, unique reversible names, terminal action exclusion, and 300 sampled transitions. `python profile_fixture_self_check.py` exercises complete unusual phase, pending, reserve, depletion, zone, and five-player fixtures. A focused source-only probe additionally checks inventory, all beanometer thresholds, field protection, deterministic setup, terminal field scoring, and the printed tie direction.
