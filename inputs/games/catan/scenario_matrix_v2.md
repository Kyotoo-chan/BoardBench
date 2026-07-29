# CATAN V2 approval matrix

- status: **frozen-for-v2-intervention-comparison-r3**
- scope: Illustrated beginner setup for 3 and 4 players; strict roll-trade-build; variable setup and experienced merged phases excluded
- claims: 125 total; 99 required clear
- scenarios: 55 (40 clear, 15 human decision)

| ID | Basis | Facts | Expectation |
|---|---|---|---|
| `CAT-R01A-3p-board-pieces` | clear | `CAT-C-SETUP-BOARD`, `CAT-C-SETUP-PIECES`, `CAT-C-SETUP-3P-RED`, `CAT-C-SETUP-ROBBER` | The exact page-1 19-hex terrain/number/harbor layout is used; robber is on the central desert; all red roads/settlements are absent; blue, orange and white each have the two pictured settlements and roads and remaining stock 13 roads, 3 settlements, 4 cities. |
| `CAT-R01B-3p-starting-resources` | clear | `CAT-C-SETUP-START-RES` | With red A removed: blue B has wood 1, brick 1, wool 0, grain 0, ore 1; orange C has wood 0, brick 0, wool 0, grain 2, ore 1; white D has wood 1, brick 0, wool 1, grain 0, ore 1. |
| `CAT-R01C-3p-bank-deck-start` | clear | `CAT-C-SETUP-BANK`, `CAT-C-SETUP-DEV` | Open bank counts are wood 17, brick 18, wool 18, grain 17, ore 16; the shuffled face-down development deck has 25 cards; the designated start seat has a legal initial roll. |
| `CAT-R02A-4p-board-pieces` | clear | `CAT-C-SETUP-BOARD`, `CAT-C-SETUP-PIECES`, `CAT-C-SETUP-ROBBER` | The exact page-1 19-hex terrain/number/harbor layout is used; robber is on the central desert; red, blue, orange and white each have the two pictured settlements and roads and remaining stock 13 roads, 3 settlements, 4 cities. |
| `CAT-R02B-4p-starting-resources` | clear | `CAT-C-SETUP-START-RES` | Red A has wood 2, brick 0, wool 0, grain 1, ore 0; blue B has wood 1, brick 1, wool 0, grain 0, ore 1; orange C has grain 2 and ore 1 only; white D has wood 1, wool 1 and ore 1 only. |
| `CAT-R02C-4p-bank-deck-start` | clear | `CAT-C-SETUP-BANK`, `CAT-C-SETUP-DEV` | Open bank counts are wood 15, brick 18, wool 18, grain 16, ore 16; the shuffled face-down development deck has 25 cards; the designated start seat has a legal initial roll. |
| `CAT-R03-player-range` | human_decision | `CAT-M-PLAYER-RANGE` | Approved constructors accept 3 and 4, reject 2 and 5; separate probes check setup, initial action and bounded playability. |
| `CAT-R04A-board-inventory` | clear | `CAT-C-INV-LAND-TOTAL`, `CAT-C-INV-WALD`, `CAT-C-INV-WEIDE`, `CAT-C-INV-ACKER`, `CAT-C-INV-HUEGEL`, `CAT-C-INV-GEBIRGE`, `CAT-C-INV-WUESTE`, `CAT-C-INV-HARBORS`, `CAT-C-INV-NUMBERS` | Assert 19 land hexes exactly: wood 4, wool 4, grain 4, brick 3, ore 3, desert 1; nine harbors; and 18 number tokens with one each 2/12 and two each 3/4/5/6/8/9/10/11. |
| `CAT-R04B-resource-inventory` | clear | `CAT-C-INV-RESOURCES` | Across bank and all player hands, assert exactly 19 each of wood, brick, wool, grain and ore (95 total) in both 3p and 4p setup. |
| `CAT-R04C-development-inventory` | clear | `CAT-C-INV-DEV-TOTAL`, `CAT-C-INV-KNIGHTS`, `CAT-C-INV-PROGRESS-TOTAL`, `CAT-C-INV-PROGRESS-DISTRIBUTION`, `CAT-C-INV-VP` | Across deck and hands, assert 25 total: 14 Knights, exactly two each Road Building/Year of Plenty/Monopoly, and five victory-point cards. |
| `CAT-R04D-player-and-other-inventory` | clear | `CAT-C-INV-ROADS`, `CAT-C-INV-SETTLEMENTS`, `CAT-C-INV-CITIES`, `CAT-C-INV-ROBBER`, `CAT-C-INV-SPECIAL-CARDS` | Assert each participating color totals 15 roads, 5 settlements and 4 cities across board/supply; additionally one robber and both represented special cards. Physical accessory counts remain source-visible but unscored. |
| `CAT-R05A-oldest-seat-starts` | clear | `CAT-C-START-OLDEST` | At initial state, active_player equals configuration.oldest_player and that seat has the legal initial roll. |
| `CAT-R05-clockwise-turn` | clear | `CAT-C-CLOCKWISE` | Completing a turn advances to the left-neighbor seat. |
| `CAT-R06-strict-phases` | clear | `CAT-C-TURN-PHASES`, `CAT-C-TURN-STRICT` | Roll precedes trade, trade precedes build, and trade cannot resume after entering build. |
| `CAT-R07-production` | clear | `CAT-C-PROD-ALL`, `CAT-C-PROD-SETTLEMENT`, `CAT-C-PROD-CITY`, `CAT-C-PROD-ADDITIVE` | A scripted non-seven pays every adjacent settlement one and city two, including multiple entitlements. |
| `CAT-R08-desert-robber-block` | clear | `CAT-C-PROD-DESERT`, `CAT-C-PROD-ROBBER` | Desert never pays and an occupied producing hex pays nobody. |
| `CAT-R09-development-timing` | clear | `CAT-C-DEV-ANYTIME`, `CAT-C-DEV-ONE`, `CAT-C-DEV-NOT-BOUGHT` | An older eligible card may play before roll; a second play and a same-turn purchase are illegal. |
| `CAT-R10-domestic-trade-rules` | clear | `CAT-C-TRADE-ACTIVE`, `CAT-C-TRADE-FREE`, `CAT-C-TRADE-NO-GIFT`, `CAT-C-TRADE-RESOURCES`, `CAT-C-TRADE-REPEAT` | Arbitrary positive resource bundles involving the active player are possible repeatedly; gifts, development cards and non-active-only transfers are rejected. |
| `CAT-R11-bilateral-consent` | human_decision | `CAT-M-TRADE-PROTOCOL` | A finite one-partner offer is built by add-one-resource actions, never by enumerating bundle subsets; construction changes no holdings; partner rejection/cancel changes nothing; acceptance transfers full positive bundles atomically. |
| `CAT-R12-maritime-rates` | clear | `CAT-C-MARITIME-4`, `CAT-C-MARITIME-3`, `CAT-C-MARITIME-2`, `CAT-C-HARBOR-ACCESS` | Each rate and port ownership works; wrong specialized resource is rejected. |
| `CAT-R13-new-harbor-delay` | clear | `CAT-C-HARBOR-DELAY` | A harbor settlement built after trade cannot be used in that turn. |
| `CAT-R14-building-costs-stock` | clear | `CAT-C-COST-ROAD`, `CAT-C-COST-SETTLEMENT`, `CAT-C-COST-CITY`, `CAT-C-COST-DEVELOPMENT`, `CAT-C-BUILD-STOCK`, `CAT-C-BUILD-REPEAT` | Each purchase removes exact resources and stock; repeated builds/buys are allowed while affordable; no build beyond stock. |
| `CAT-R15-road-legality` | clear | `CAT-C-ROAD-EMPTY`, `CAT-C-ROAD-CONNECT`, `CAT-C-ROAD-BLOCK` | Reject occupied/disconnected edges and continuation through an opponent building; allow valid own connection. |
| `CAT-R16-settlement-legality` | clear | `CAT-C-SETTLE-ROAD`, `CAT-C-SETTLE-DISTANCE` | Require own incident road and empty target/adjacent vertices. |
| `CAT-R17-city-upgrade` | clear | `CAT-C-CITY-UPGRADE`, `CAT-C-SETTLE-RETURN` | Only own settlement upgrades; same vertex becomes city and settlement returns to stock. |
| `CAT-R18-longest-threshold-branch` | clear | `CAT-C-LR-THRESHOLD`, `CAT-C-LR-BRANCH` | Four does not qualify, five does, and branch edges are not summed. |
| `CAT-R19-longest-interruption` | clear | `CAT-C-LR-OPP-BLOCK`, `CAT-C-LR-OWN-NOT-BLOCK` | Opponent building splits a route; own building does not. |
| `CAT-R20-longest-transfer-ties` | clear | `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, `CAT-C-LR-VACANT-TIE` | Strictly longer route transfers; after interruption, incumbent retains a tied lead and a leading tie excluding incumbent leaves the card vacant. |
| `CAT-R21-longest-cycles` | human_decision | `CAT-A-LR-CYCLE` | Loop and figure-eight fixtures compute maximum edge-simple trail without edge reuse and with opponent blockers. |
| `CAT-R22-seven-discard` | clear | `CAT-C-SEVEN-NO-PROD`, `CAT-C-DISCARD-THRESHOLD`, `CAT-C-DISCARD-AMOUNT`, `CAT-C-DISCARD-RESOURCE-ONLY`, `CAT-C-SEVEN-SEQUENCE` | Seven pays nothing; sizes 7/8/9/11 discard 0/4/4/5 resources; development cards do not count; trade remains locked until discard, move and robbery finish. |
| `CAT-R23-robber-move-steal` | clear | `CAT-C-ROBBER-MOVE`, `CAT-C-ROBBER-CHOOSE`, `CAT-C-ROBBER-STEAL` | Must move to a different land hex and choose among adjacent opponents; when the selected victim has resources, exactly one blind resource card transfers and development cards never do. |
| `CAT-R24-knight-no-discard` | clear | `CAT-C-KNIGHT-NO-DISCARD`, `CAT-C-KNIGHT-MOVE`, `CAT-C-KNIGHT-STEAL` | Knight immediately moves robber and permits one adjacent robbery without seven-discard checks. |
| `CAT-R25-random-theft-no-victim` | human_decision | `CAT-M-RNG`, `CAT-M-NO-VICTIM` | Same seed reproduces rolls/deck/theft selection; transfers preserve card counts; an adjacent empty chosen hand or no adjacent opponent transfers nothing. |
| `CAT-R26-private-simultaneous-discards` | human_decision | `CAT-M-DISCARD-PROTOCOL` | Choices are private until complete and apply together; public pending data reveals quantities/completion but not identities. |
| `CAT-R27-development-purchase` | clear | `CAT-C-DEV-BUY-TOP` | Purchase takes top deck card privately and decrements deck. |
| `CAT-R28-road-building` | clear | `CAT-C-ROAD-BUILDING` | Road Building charges no resources and two sequential placements obey normal road rules when two are feasible. |
| `CAT-R29-year-of-plenty` | clear | `CAT-C-YOP` | Takes any two available resources including a matching pair. |
| `CAT-R30-monopoly` | clear | `CAT-C-MONOPOLY` | Transfers all opponent cards of one resource and none of other resources. |
| `CAT-R31-played-card-zones` | clear | `CAT-C-PROGRESS-REMOVED`, `CAT-C-KNIGHT-FACEUP` | Progress leaves play while Knight remains face-up and public. |
| `CAT-R32-largest-army` | clear | `CAT-C-ARMY-THRESHOLD`, `CAT-C-ARMY-TRANSFER` | First three gets award; tie retains; strictly larger count transfers. |
| `CAT-R33-score-components` | clear | `CAT-C-SCORE-SETTLEMENT`, `CAT-C-SCORE-CITY`, `CAT-C-SCORE-AWARDS`, `CAT-C-SCORE-VP` | Public and total scoring values match every source-defined point object. |
| `CAT-R34-active-immediate-win` | clear | `CAT-C-WIN-ACTIVE`, `CAT-C-WIN-IMMEDIATE` | Active player reaching ten terminates immediately with no legal actions. |
| `CAT-R35-offturn-no-win` | clear | `CAT-C-WIN-OFFTURN` | Non-active player at ten remains nonterminal, then wins immediately upon becoming active before rolling if still at ten. |
| `CAT-R36-vp-win-exception` | clear | `CAT-C-VP-WIN-EXCEPTION` | A newly bought VP card may immediately establish active-player victory despite same-turn restriction. |
| `CAT-R37-minimal-vp-reveal` | human_decision | `CAT-M-VP-REVEAL` | Only the minimum cards needed for ten reveal, in hand order. |
| `CAT-R38-source-privacy` | clear | `CAT-C-INFO-RESOURCE-PRIVATE`, `CAT-C-INFO-DEV-PRIVATE` | Own identities visible; opponent resource/development identities and hidden victory points remain hidden. |
| `CAT-R39-observation-convention` | human_decision | `CAT-M-HAND-COUNTS`, `CAT-M-INFO-DEV-COUNT` | Observations expose resource hand sizes, face-down development counts, bank, board and visible score without private identities or hidden victory points. |
| `CAT-R40-shortage-package` | human_decision | `CAT-M-BANK-PRODUCTION`, `CAT-M-BANK-ACTIONS`, `CAT-M-ROAD-BUILDING-SHORT`, `CAT-M-DEV-EMPTY` | Production is all-or-none per resource across entitlements; bank actions require full stock; development purchase needs deck card; Road Building places maximum feasible up to two. |
| `CAT-R41-designated-oldest-start` | human_decision | `CAT-M-OLDEST-INPUT` | The profile designates player 0 as the oldest seat; player 0 is active and has the initial legal roll in both 3p and 4p games. |
| `CAT-R42-development-boundaries` | human_decision | `CAT-M-DEV-BOUNDARY` | Subject to the one-card-per-turn limit, an eligible active-player development card may interrupt pending discard, seven-sourced robber and bilateral-consent decisions; it resolves on top, then the exact interrupted state resumes unless terminal. |
| `CAT-R43-victory-during-card-effect` | human_decision | `CAT-M-TERMINAL-SUBACTION` | Victory after the first committed Road Building road or other atomic subaction terminates immediately and cancels the remaining effect. |
| `CAT-R44-finite-trade-bound` | human_decision | `CAT-M-TRADE-OFFER-BOUND` | Incremental give/take totals stop at the respective public hand sizes without using private resource identities; unaffordable accepted bundles remain impossible. |
| `CAT-R45-discard-escrow-interrupt` | human_decision | `CAT-M-DISCARD-ESCROW` | A submitted private selection cannot be transferred or invalidated by an interrupt; all escrowed selections settle together without negative counts. |
| `CAT-R46-knight-robbery-required` | human_decision | `CAT-X-KNIGHT-DECLINE` | After a Knight move with an adjacent opponent, a victim choice is required; choosing an empty adjacent hand transfers nothing and resumes the interrupted phase. |
| `CAT-R47-maritime-receive-differs` | human_decision | `CAT-A-MARITIME-SAME` | Same-resource 4:1, 3:1 and 2:1 maritime actions are illegal. |

## Numbering

Numeric stems now extend through `R47`. The explicit setup/inventory splits `R01A`–`R01C`, `R02A`–`R02C`, and `R04A`–`R04D` produce 55 physical scenarios without renumbering prior stable IDs; `R40`–`R47` are intentionally contiguous.

## Approval boundary

No implementation or scoring starts until this complete matrix is approved. Claim mapping is not assertion completeness; each executable scenario will retain direct source evidence for every mapped fact.
