# Rule coverage

The implementation models the supplied 2022 German base game on the illustrated beginner board. `GAME_PROFILE.json` supplies identifiers and payload representation only.

| Source section / named rule | Implementing symbol(s) | Probe or exclusion | Assumption |
|---|---|---|---|
| Spielanleitung p.1 Spielübersicht; Startaufstellung für Einsteiger | `Game.initial_state`, `HEXES`, `SETUP`, `HARBORS` | Initial 3/4-player state and inventories round-trip in both self-checks. | None |
| Spielanleitung p.2 Vorbereitung | `Game.initial_state`, `DEV_INVENTORY` | Source-only initial inventory/resource probe. | None |
| Spielablauf: würfeln, handeln, bauen | `legal_actions`, `apply_action`; phases `roll`, `trade`, `build` | Random rollout traverses all three phases. | None |
| Rohstofferträge; settlement 1 / city 2; robber blocks; shortage | `_produce` | Source-only scripted-roll probes; all-or-none shortage follows profile representation choice. | None |
| Binnenhandel | trade-offer actions and `apply_action` | Offer construction/accept/reject reachable from every trade phase. | A-03 |
| Seehandel 4:1, 3:1, 2:1 | `_trade_ratios`, `maritime_trade` | Legal-action resource/bank availability probe. | None |
| Bauen; return paid resources to supply | `_can_pay`, `_pay` | Every exposed paid build is accepted. | None |
| Straße: Holz + Lehm; connection; one per edge | `_legal_road_edges`, `_connected_road`, `_place_road` | Source-only fixtures for empty/connected edge and 0/1/2 stock. | None |
| Siedlung: Holz + Lehm + Wolle + Getreide; road connection; Abstand | `_legal_settlement_vertices`, `_place_building` | Source-only adjacency and distance probes. | None |
| Stadt: 3 Erz + 2 Getreide; upgrade only; two points/production | city actions, `_produce`, `_score` | Source-only upgrade and production probes. | None |
| Entwicklungskarte: Erz + Wolle + Getreide; hidden hand | buy action, observation serialization | Opponent identities hidden; own hand retained. | None |
| One development card per turn; not bought this turn; before rolling | `_eligible_devs`, `_dev_actions`, `_play_development` | Rollout plus fixture reconstruction. | None |
| Ritter | `_play_development`, `_push_robber`, `_move_robber`, `_steal` | Source-only move/victim/private theft probes. | None |
| Fortschritt: Straßenbau | road-building pending frame, `place_free_road` | 0/1/2 road-stock and feasibility probes. | None |
| Fortschritt: Erfindung | `play_year_of_plenty` | Enumerates only bank-available pairs. | None |
| Fortschritt: Monopol | `play_monopoly` | Source-only transfer probe across all opponents. | None |
| Siegpunktkarten | `_score`, `_check_victory`, observations | Hidden points excluded from public score; minimum reveal on win. | A-01 |
| Sieben gewürfelt: discard half, move robber, steal | `_start_seven`, discard actions, `_move_robber`, `_steal` | Scripted rolls/theft and pending fixture round-trips. | None |
| Räuber production blocking | `_produce` | Source-only roll with robber on productive hex. | None |
| Längste Handelsstraße | `_longest`, `_recalculate_specials` | Threshold, branch, loop, own/opponent interruption, transfer and tie logic audited. | A-02 |
| Größte Rittermacht | `_recalculate_specials` | Threshold 3, strict transfer, incumbent tie probe. | None |
| Spielende / 10 Siegpunkte on own turn | `_check_victory`, `returns`, terminal action suppression | Immediate award-triggered victory probe; terminal fixture has no actions. | A-01 |
| Gründungsphase / Aufbau variabel | Not implemented: profile fixes the illustrated beginner setup, which the supplied Anleitung explicitly recommends. | Source-only reason: outside fixed beginner representation. | None |
| Handeln und Bauen – Trennung aufgehoben | Not implemented: profile explicitly selects strict phases. | Source-only reason: Almanach labels this an experienced-player recommendation. | None |
| Play it smart app (Almanach pp.2–4) | Not implemented. | Optional app-mediated events are not base-game rules and require an external app. | None |
| Taktik; Wege; Kreuzung; Küste; Wüste; Zahlenchips | topology helpers/constants and legality functions where mechanical | Informational/tactical text has no separate action; definitions are probed through building/production. | None |
| Almanach pp.12–22 product overview | Not implemented. | Advertising/overview of other games and expansions, not rules for the supplied base game. | None |
| Spielmaterial (Almanach p.23) | initial inventories, bank, `DEV_INVENTORY` | Counts audited at initial state; removed 3-player red stock represented by configuration. | None |
| Impressum (Anleitung p.4; Almanach pp.4,24) | Not applicable. | Bibliographic matter, no game behavior. | None |
