# Rule coverage — 4–5-player augmented Bohnanza

Source priority: `game_rules.pdf` is authoritative gameplay evidence;
`game_components.pdf` is used only for the observed 129-card inventory, bean
identities, and printed harvest thresholds. Probes below are source-only checks
that can be performed against public symbols and constructed `GameState` values.

| Supplied section / named rule or card | Implementing symbol | Source-only probe or reason not probed | Assumption |
|---|---|---|---|
| Grundspiel — Spielmaterial & Spielvorbereitung; 4–5 players; two fields | `Game.__init__`, `Game.initial_state`, `GameState.fields` | Initialize 4 and 5 players; each has two empty fields | — |
| Start player/card; clockwise turns | `GameState.active`, `apply_action` phase-4 completion | Player 0 starts; successor is `(active+1)%players`; marker has no separate mechanical action | — |
| 104 base cards / eight base sorts | `BEANS`, `initial_state` | Sum the eight base entries = 104 | — |
| Five individually dealt ordered hand cards | `initial_state`, `hands` | Each initial hand has five cards; phase 1 only exposes index 0 for planting | — |
| Hand order never changes / new cards go behind last | phase-1 `pop(0)`; accepted-trade indexed removal; phase-4 `append` | Check front-only phase-1 action and append behavior | — |
| Draw and discard piles | `deck`, `discard`, `_draw_one`, `_harvest` | Harvest discards unused cards; depletion reshuffles discard | A-03 |
| Spielablauf — four phases | `phase`; `legal_actions`; `apply_action` | Roll phase1 → phase2_draw/trade → phase3 → phase4 | — |
| Wichtige Regeln für den Bohnenanbau: one sort per field; same sort on multiple fields | `_plant_fields` | Compatible and empty fields legal; incompatible occupied fields absent | — |
| Phase 1: mandatory front bean, optional second, never third | `phase1_planted`, phase-1 actions | First has no skip; second has skip; transition after two | — |
| Empty hand skips phase 1 | `legal_actions`: `Phase 2 beginnen` | Construct empty active hand | — |
| Required planting with no suitable field requires harvest first | `_plant_fields`, `_harvest_actions` | Full incompatible fields yield no plant action and legal harvest actions subject to protection | — |
| Phase 2: reveal top two; revealed cards belong to active player | `_draw_one`, `revealed`, `Zwei Bohnenkarten aufdecken` | Apply reveal and inspect up to two public cards | — |
| Only active player trades with another; others not with each other | `TradeDraft`, `Handel beginnen` | Only active selects any one nonactive partner | — |
| Trade any hand positions; active may trade revealed cards | offer/request add actions | Every current hand index and every revealed index can be added | — |
| Received cards cannot be retraded and never enter hand | `sideways`; accepted trade transition | Accepted cards enter `sideways`, which offer actions never reference | — |
| Field cards cannot be traded | offer/request actions | No field-card selection action exists | — |
| Unequal card counts / bundles | incremental `TradeDraft` selection | Build arbitrary-sized offered/requested index sets, including 2-for-1 | — |
| Both players consent; do not remove before agreement | `awaiting_consent`, accept/reject transitions | Proposal changes decision player but no cards; reject preserves cards | — |
| Gifts require recipient consent | proposal with only offered cards; accept/reject | Draft nonempty one-sided offer and propose | — |
| Continue hand trading after revealed cards traded; active ends phase | trade loop; `Handelsphase beenden` | Accept trade returns to active with trade phase unchanged | — |
| Phase 3: all sideways and untraded revealed cards must be planted; owner chooses order | `plant_queue`, phase-3 indexed actions | Queue contains both sources; any queued card owned by decision player can be selected | — |
| Phase 4 augmented rule: each player draws one, active first, clockwise | `draw_order`, `Eine Bohnenkarte nachziehen` | Expected order `[active,...]`, one append each | A-01 |
| Die Bohnenernte: voluntary at any time, including nonactive players | `_harvest_actions`, decision-owner harvest opportunities | Probe harvest at active, trade-consent, and phase-3 decisions | A-02 |
| General Bohnometer scoring; turn earned cards to coins; remainder discard; field empty | `_harvest`, `BEANS`, `coins`, `discard` | Construct threshold-size fields and harvest | — |
| Saubohne example 1–2/3–4/5–6/7/8+ gives 0/1/2/3/4 | `BEANS["Saubohne"]` | Threshold tuple is `(3,5,7,8)` | — |
| Feuerbohne example: 3 cards gives 1 coin | `BEANS["Feuerbohne"]`, `_harvest` | Construct three-card field | — |
| Bohnenschutzregel | `_harvestable` | Single field blocked iff another own field has >1 card | — |
| Ein leerer Nachziehstapel: reshuffle discard | `_draw_one` | Draw last card with nonempty discard and depletion <3 | A-03 |
| Spielende: third empty; if during phase 2 finish phases 2 and 3 | `depletion_count`, `end_after_phase3`, `_finish` | Force third depletion on reveal and verify trading/planting remain before terminal | — |
| Final field harvest; hands ignored; each coin-card worth one | `_finish`, `coins` | Terminal score uses existing coins plus field yields and never hand contents | — |
| Winner most coins; tie farthest clockwise from start player | `_finish`, `winners`, `returns` | Equal scores choose greatest seat index because start player is fixed at 0 | — |
| Augmented variant — Ackerbohnen for 4–5; base sorts + Ackerbohne + Weinbrandbohne | `BEANS`, `initial_state` | Deck composition contains exactly the ten supplied sorts | A-01 |
| Every player starts with two fields | `initial_state` | Covered above | — |
| Ackerbohne harvest: 2 unlocks third field, cards discarded, existing first/two fields retained | `_harvest`, `third_field`, `fields.append` | Construct two-card field and verify third empty field plus unchanged other field | — |
| Two Ackerbohnen with third field already: no yield | `_harvest` | Set `third_field=True`, harvest two, coins unchanged | — |
| Three Ackerbohnen: three coins, no third-field unlock | `_harvest` | Construct three-card field | — |
| Komponenten: exactly 129 cards | `BEANS`, `initial_state` | Counts sum to 129; dealt plus deck remains 129 | — |
| Weinbrandbohne — 22; thresholds 4/7/9/11 | `BEANS["Weinbrandbohne"]` | Direct constant probe | — |
| Blaue Bohne — 20; thresholds 4/6/8/10 | `BEANS["Blaue Bohne"]` | Direct constant probe | — |
| Feuerbohne — 18; thresholds 3/6/8/9 | `BEANS["Feuerbohne"]` | Direct constant probe | — |
| Saubohne — 16; thresholds 3/5/7/8 | `BEANS["Saubohne"]` | Direct constant probe | — |
| Brechbohne — 14; thresholds 3/5/6/7 | `BEANS["Brechbohne"]` | Direct constant probe | — |
| Sojabohne — 12; thresholds 2/4/6/7 | `BEANS["Sojabohne"]` | Direct constant probe | — |
| Augenbohne — 10; thresholds 2/4/5/6 | `BEANS["Augenbohne"]` | Direct constant probe | — |
| Rote Bohne — 8; thresholds 2/3/4/5 | `BEANS["Rote Bohne"]` | Direct constant probe | — |
| Gartenbohne — 6; 1→0, 2→2, 3+→3 coins; no 1/4 tier | special branch in `_harvest` and `_finish` | Construct sizes 1, 2, 3, and >3 | — |
| Ackerbohne — 3; special harvest | special branch in `_harvest` and `_finish` | Covered above | — |
| Excluded Kaffee-, Kakao-, Auftrags-, Elsterbohnen, AMIGO coins, other editions | absence from `BEANS` | Set comparison against the ten names | — |
| Card anatomy / threshold reading / coin side | `BEANS`, `_harvest` | Threshold count computes attained tiers; coins are integer score because card identities cease to matter | — |
| Komponenten “Sorten im Detail” prose and Deck-Checkliste | `BEANS` | Every named row and count/threshold is individually mapped above | — |
| Official-source bibliography in user aid | none | Attribution only; no gameplay mechanic to probe, and external links were not used | — |
| Action names stable, unique, reversible, source-labelled | `action_to_name`, `name_to_action` | Required self-check enumerates and round-trips every legal action | — |
| Private information | `render` | Current decision player's ordered hand shown; opponents represented only by counts | — |
| Terminal states expose no actions and return utilities | `legal_actions`, `returns` | Required self-check tests terminal action condition when reached | — |

## Explicit conflicts and limits

The component aid calls itself unofficial and does not override gameplay. No direct
count/threshold contradiction with the supplied publisher pages was found. The
missing referenced variant text and decision scheduling are recorded as A-01 and
A-02; the empty-deck edge case is A-03.
