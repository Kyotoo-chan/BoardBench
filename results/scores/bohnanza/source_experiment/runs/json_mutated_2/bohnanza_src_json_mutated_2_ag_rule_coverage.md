# Rule coverage: 4–5-player Ackerbohnen condition

Only the publisher pages govern play. `game_components.json` supplies observed names,
counts, and printed Bohnometers; its material conflict is A-01.

| Supplied section / named rule | Implementing symbol | Source-only probe / disposition | Assumption |
|---|---|---|---|
| Cover/title (p.1) | module scope | Identification only; no mechanic | — |
| Grundspiel material and preparation (p.2) | `COUNTS`, `BOHNOMETER`, `Game.initial_state` | 4/5 players, two fields, start player, five-card hands; variant overrides deck membership | A-01 |
| Eight base beans: Blaue, Feuer-, Sau-, Brech-, Soja-, Augen-, Rote, Gartenbohne (p.2) | `COUNTS`, `BOHNOMETER` | All names/counts/printed schedules represented | — |
| Coffee, Weinbrand, Cocoa and Acker used only in variants (p.2) | `COUNTS` | Variant 2 includes only Weinbrand and Acker; coffee/cocoa audited but excluded by p.11 | A-01 |
| Hand order / no sorting; draw pile/discard; clockwise setup (p.3) | `hands`, `deck`, `discard`, `active` | Ordered list, append-only drawing, pop-front planting | A-03 |
| Four phases and clockwise active player (p.4) | `stage`, `apply_action` | Phase progression and active increment represented | — |
| Bean-field construction; one type per field, same type on multiple fields, overlap rows (p.4) | `_plantable_fields`, `fields` | Type legality represented; overlap is presentation only | — |
| Phase 1: mandatory first, optional second, never third hand card (pp.4–5) | `plant_first`, `plant_second` actions | First advances only after planting; second has skip; no third | — |
| Must harvest before otherwise impossible planting; empty-hand phase skip (p.5) | `_can_harvest`, `advance_plant` | Legal harvest permits creation of compatible/empty field | — |
| Phase 2: reveal top two, own them, trade or plant (p.5) | `reveal_two`, `table`, `trade` | Two ordered draws and active ownership represented | A-03 |
| Trade rules: active with any players; others not mutually; any hand positions; active may trade revealed; received cards not retraded; field cards not traded; unequal quantities (pp.5–6) | `offer_trade`, `accept_offer`, `table` | One-for-one atomic proposals can be repeated, thereby allowing unequal aggregate quantities; table acquisitions cannot be offered again | — |
| Offer commitment requires both consent (p.6) | `respond`, `accept_offer`, `decline_offer` | Target explicitly accepts or rejects before cards move | — |
| Acquired cards lie beside fields, never enter hand (p.6) | `table` | Accepted cards remain owner-tagged table cards | — |
| Gifts require recipient consent (p.6) | `offer_gift`, response actions | Explicit consent represented | — |
| Active ends trading (p.6) | `finish_trading` | Always available in trade stage | — |
| Phase 3: all traded/revealed cards planted; owners choose order; active must plant untraded revealed (p.7) | `plant_table`, `pending_order` | All owner-tagged cards mandatory; fixed first-card order within an owner | — |
| Forced harvest before incompatible table planting (p.7) | harvest actions in `plant_table` | Harvest remains legal until a planting field exists | — |
| Base Phase 4 draws three to active player (p.7) | not implemented | Explicitly overridden for this condition by Variant 1 (p.10) | — |
| Harvest anytime; Bohnometer; coin cards flipped, remainder discarded; field becomes empty (pp.7–8) | `_harvest`, `BOHNOMETER` | Threshold lookup, coin removal, discard, clear field | A-02 |
| Bean protection rule (p.8) | `_can_harvest` | Singleton blocked iff any other field has more than one | — |
| Empty draw pile: shuffle discard into new face-down pile (p.9) | `_take_card` | First/second exhaustion reshuffle discard | A-03 |
| Base end: third emptying; finish phases 2/3 if during reveal; harvest all fields; hands ignored; most coins; clockwise-furthest tie break (p.9) | `_take_card`, `_finish_game`, `returns` | Variant keeps third-empty rule for 4+; all fields are harvested automatically before winner calculation | — |
| Variant 1 continuation: five-card start, four phases; Phase 4 each player draws one active-first clockwise (p.10) | `initial_state`, `draw_order`, `draw_one` | Composed into Variant 2 as directed | — |
| Variant 1 end: 3 players second empty, 4+ third empty (p.10) | `_take_card` | Assigned 4/5 condition uses third empty | — |
| Variant 2 material: 4–5, all base + Acker + Weinbrand, two fields; follows Variant 1 (p.10) | `Game.__init__`, `COUNTS`, setup/stages | Both supported player counts; 129-card publisher deck | A-01 |
| Ackerbohne harvest: two on first/second field grants immediate third field and no coins; later two yields nothing; three yields three coins (p.11) | `_harvest` | Field-count branch and exact rewards represented | — |
| Weinbrandbohne (named variant card) | `COUNTS`, `BOHNOMETER` | 22 cards and observed printed thresholds represented | — |
| Kaffeebohne, Kakaobohne (named supplied observation) | excluded from `COUNTS` | Audited; publisher Variant 2 does not include them | A-01 |
| Elsterbohne, Auftrag cards, AMIGO coin cards (named supplied observation) | not implemented | Observation says absent; no supplied gameplay rules | — |

## API probes

`agentic_self_check.py` exercises setup, all reachable legal actions by deep copy,
name/action round trips, transitions, terminal action suppression, and returns.
The two exact validation commands listed in the task are the executable probes.
