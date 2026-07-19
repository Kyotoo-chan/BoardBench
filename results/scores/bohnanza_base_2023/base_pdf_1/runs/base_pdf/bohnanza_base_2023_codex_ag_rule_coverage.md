# Rule coverage

Only the supplied two-page rulebook is gameplay evidence. Contract/profile checks are representation probes.

| Source section / named rule | Implementing symbol | Probe or audit note | Assumption |
|---|---|---|---|
| Spielidee; most coins wins | `returns`, `METERS` | terminal scoring and meter thresholds exercised by direct states | A-03 utility encoding |
| Spielmaterial & Spielvorbereitung; 3–5 players, 3 fields for 3 / 2 otherwise, five ordered hand cards, 104-card distribution | `Game.__init__`, `initial_state`, `COUNTS` | initial inventory/field/hand inspection; fixture checks 4/5 players | A-01 first player |
| Hand order must never change; front card visible | `initial_state`, `apply_action` plant/draw | planting only index 0; draws append | none |
| Spielablauf; four phases, clockwise active person, start card remains | `PHASES`, `apply_action` | rollout phase transitions | start card represented by `start_player`; A-01 |
| Bohnenanbau; same sort per field, same sort may occupy multiple fields, cards stacked | `_plant_actions`, plant transition | legal destination filtering | none |
| Phase 1; mandatory first, optional second, no-hand skips | `legal_actions`, plant/pass transitions | rollout plus phase fixtures | none |
| Die Bohnenernte; harvest at any time, meter rewards, harvested field empties | `_harvest_actions`, harvest transition, `METERS` | every legal harvest is applied by self-check | none |
| Bohnenschutzregel | `_harvest_actions` | singleton suppressed when any multi-card field exists | none |
| Phase 2; reveal top two; active person alone trades; hand/revealed cards; acquired cards cannot retrade; unequal quantities; gifts require consent | trade actions, `pending`, `pending_received`, trade accept/reject | consent fixture and rollout action application | A-02 bundle bound |
| Phase 3; all traded and untraded revealed cards mandatory, freely ordered; harvest if needed | `plant_received`, `_plant_actions`, harvest actions | phase fixture and rollouts | both received and revealed sources are offered together |
| Phase 4; draw three in order, append to hand, next player left | `_draw_one`, draw transition | deterministic seeded rollouts | none |
| Ein leerer Nachziehstapel; reshuffle discard and continue | `_draw_one` | source-only constructed depletion states | none |
| Ende des Spiels; third deck exhaustion; finish phases 2/3 if exhaustion occurs while revealing; harvest all fields; hand ignored; tie farthest clockwise from start wins | `_draw_one`, `_finish`, `returns` | terminal constructed states | A-03 utility encoding |
| Card names/counts: Garten 6, Rot 8, Augen 10, Soja 12, Brech 14, Sau 16, Feuer 18, Blau 20 | `BEANS`, `COUNTS` | initial inventory count | none |
| Beanometers on all eight named cards | `METERS` | direct threshold probes | thresholds transcribed from supplied card images |

## Explicit unresolved source/model gaps

The profile has no negotiation-message action, so proposals are concrete card bundles. The rulebook does not prescribe how an API chooses the first player.
