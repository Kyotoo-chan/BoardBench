# Rule coverage — assigned 4–5-player condition

The publisher rulebook is authoritative for play. `game_components.json` is used only for observed card counts and printed harvest meters. Symbols refer to `implementation.py`.

| Source section / named item | Implementing symbol | Source-only probe / disposition | Assumption |
|---|---|---|---|
| p2 Spielmaterial; 4–5 player board; start-player card; overview cards | `Game.initial_state`, `GameState.active` | 4/5 accepted and other counts rejected; non-functional aids not modeled | — |
| p2 eight base beans and counts: Gartenbohne 6, Rote Bohne 8, Augenbohne 10, Sojabohne 12, Brechbohne 14, Saubohne 16, Feuerbohne 18, Blaue Bohne 20 | `BEANS`, `COUNTS`, `METERS` | constants auditable directly against page/component observation | — |
| p2 note: Kaffee, Weinbrand, Kakao, Acker, Elster only in variants | `BEANS` | assigned p10 variant includes only Weinbrand and Acker; Kaffee/Kakao/Elster excluded | — |
| p3 setup: shuffle, five individually dealt hand cards, order immutable, draw/discard piles, two fields | `initial_state`, ordered `hands`, `deck`, `discard`, `fields` | initial hand lengths 5, fields length 2 | A-03 |
| p4 turn clockwise; start card stays; four phases | `active`, `phase`, `draw_three` transition | rollout observes cyclic active player and phase sequence | — |
| p4 same-type-only fields; no simultaneous planting on multiple fields; cards overlap | `_can_plant`, `plant_hand`, `plant_trade` | mismatched-field plant absent from legal actions | — |
| p4 phase 1: mandatory first/front card, optional second/front card, never third | `plant_first`, `plant_second`, `skip_second` | only index 0 is consumed; second phase has skip | — |
| p5 no hand cards at phase start skips to phase 2 | `advance` | action exposed only for empty first-plant hand | — |
| p5 phase 2: reveal top two and own them; trade or plant later | `reveal_two`, `face_up`, `trade` | exactly two draw attempts, both enter face-up pool | — |
| p5–6 active player trades; others cannot trade together; all hand cards and two face-up eligible; unequal quantities permitted; received cards cannot be retraded or enter hand; field cards cannot trade | proposal actions, `respond`, `planting` | legal offers always involve active and one target; acquired cards enter planting queue | A-01 |
| p6 card leaves hand only when deal succeeds; both agree; gifts need consent; end trade voluntarily | `accept`, `reject`, `propose_gift`, `finish_trading` | rejected offer leaves cards unchanged | A-01 |
| p7 phase 3: all traded/received and untraded face-up cards mandatory; players choose order | `plant_trades`, `plant_trade` | every queued card must plant before finish action | Queue order follows accepted-deal order; source does not formalize simultaneous ordering (non-material because each owner may harvest between cards). |
| p7 phase 4: active draws three behind hand without reordering; next left player | `draw_three` | append-only draw and modulo transition | — |
| p7–8 harvest only on active turn; harvest meter; coin cards to taler pile, rest discard; zero-coin harvests possible | `_harvest_actions`, `_harvest`, `METERS`, `coins`, `discard` | harvest actions occur only for controller during that player's required planting; gain computed at greatest met threshold | — |
| p8 field protection: singleton field cannot be harvested while another field has more than one | `_protected` | protected field omitted from legal actions | — |
| p9 empty draw pile: shuffle discard and continue | `_draw` | increments exhaustion and uses discard as new deck | A-03 |
| p9 end: third emptying; if during phase 2 finish phases 2 and 3; harvest all fields, hand cards count as talers; highest total wins; clockwise-nearest-to-start tie-break | `_draw`, `end_pending`, `draw_three`, `returns` | terminal has no legal actions; returns adds coins plus hand count | A-02 |
| p10 base flow exception for 4–5: draw three (already base); third exhaustion end | assigned p9/p10 flow | module restricted to 4/5 | — |
| p10 Variante 2 setup: base beans + Ackerbohnen + Weinbrandbohnen; two fields | `BEANS`, `COUNTS`, initial two fields | Kaffee/Kakao excluded; counts 3/22 included | — |
| p11 Ackerbohne Bohnometer: exactly 2 grants third field if absent, otherwise nothing; 3 grants 3 talers | `_harvest` Acker branch | two-card harvest appends empty third field only from two-field state; three gains 3 | — |
| Weinbrandbohne printed meter 4/7/9/11 → 1/2/3/4 | `METERS["Weinbrandbohne"]` | direct constant probe | — |
| Kaffeebohne, Kakaobohne, Elsterbohne | excluded by p10 assigned variant | named and audited; no implementation because source says use only base + Acker + Weinbrand | — |

## Deliberate abstractions

Cards converted to coins are represented by an integer score rather than retained face-down identities. Player overview cards, the start-player marker artwork, and physical field boards have no independent legal effect. Hidden hands and the ordered deck remain present in state; `render` exposes only hand sizes, not hand identities.
