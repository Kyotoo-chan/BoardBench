# Rule coverage

| Source section / named rule | Implementing symbol | Probe or reason not probed | Assumption |
|---|---|---|---|
| Spielidee | `Game`, `returns` | rollout reaches scoring | none |
| Spielmaterial & Spielvorbereitung; 104 cards; 6/8/10/12/14/16/18/20 | `BEANS`, `COUNTS`, `initial_state` | initial inventory/count probe | none |
| 3 players: 3 fields; 4–5: 2 fields | `initial_state` | profile fixture covers 4/5; direct 3-player check | none |
| Five hand cards; hand order fixed; front card visible | `initial_state`, `_plant_actions` | rollout can plant only index 0 | none |
| Start card stays with starting player | `start_player`, `initial_state` | serialization probe | A-01 |
| Four phases in order | `legal_actions`, `apply_action` | agentic rollout | none |
| Bean-field rule: one variety per field; same variety on multiple fields | `_plant_actions` | legal-action source probe | none |
| Phase 1: first card mandatory; second optional; empty hand skips | `legal_actions`, `apply_action` | rollout probes pass availability | none |
| Bean harvest required to make room | harvest actions plus planting transition | source-only structural probe | none |
| Phase 2: reveal top two; active player trades | `_draw_one`, `legal_actions` | rollout | A-02 |
| Trade rules: only active player initiates; any players; hand location irrelevant; revealed cards tradable; received/field cards not tradable; unequal counts | trade action generation | legal action enumeration/source probe | none |
| Trade consent and timing of taking cards from hand | `trade_response`, `trade_accept`, `trade_reject` | rollout/action acceptance | none |
| Traded cards placed beside fields and cannot return to hand | `pending_received` | state transition probe | none |
| Gifts require consent | `gift`, `trade_response` | action acceptance | none |
| Phase 3: all traded and remaining revealed cards must be planted; arbitrary order | `plant_received` | rollout | none |
| Phase 4: draw three behind last hand card | `draw`, `_draw_one` | rollout | A-03 |
| Harvest at any time, including off-turn | `_harvest_actions` | legal actions include all players | none |
| Beanometers (all eight cards) | `PAY` | source-table transcription probe | none |
| Harvest procedure: count, flip coin cards, discard rest, empty field | `_do_harvest` | transition probe | none |
| Bean protection rule | `_can_harvest` | legal action probe | none |
| Empty deck: shuffle discard; third depletion ends game | `_draw_one`, `_finish` | constructed source-only state probe | A-02, A-03 |
| End during phase 2 completes phases 2 and 3 | `reveal`, `plant_received` | constructed source-only state probe | A-03 |
| Final harvest, hand cards worth one each, most coins wins | `_finish`, `returns` | terminal fixture/source probe | none |
| Tie: farthest clockwise from start player | `returns` | constructed terminal state probe | A-01 |

The illustrated examples introduce no additional named card or combination rules beyond
the trade, planting, harvest, protection, and beanometer rules mapped above.
