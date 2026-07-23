# CATAN — Das Spiel (2022) — cited rule facts

- **status:** approved (2026-07-23)
- **condition:** matching official 2022 German Spielanleitung + CATAN-Almanach
- **scope:** fixed four-player beginner setup; strict roll → trade → build phases
- **excluded:** variable setup, the experienced-player merged trade/build variant, CATAN Assistant/“Play it smart,” web/remembered rules, expansions, and the archived 2015/2016 Almanach candidates

## Source register

| ID | Role | Authorship / edition | Path | SHA-256 |
|---|---|---|---|---|
| `CATAN22-RULES` | `publisher_rulebook` | KOSMOS/CATAN GmbH; © 1995, 2022; Art.-Nr. 68 26 82; PDF title `682682_Cat_Basis34_Manual_211202.indd` | `inputs/games/catan/game_rules.pdf` | `e0673fa93040f5b43908b215f52573878f586d26827d3a4f07c2ef8f8a947cf3` |
| `CATAN22-ALMANAC` | `publisher_companion` | KOSMOS/CATAN GmbH; © 1995, 2022; Art.-Nr. 68 26 82; PDF title `682682_Cat_Basis34_Almanach_211202.indd` | `inputs/games/catan/game_almanac.pdf` | `8fe89cc65308c08104a2b2afd2f8edae24e8c608383420b044a6f35cd2c611bc` |

The primary explicitly requires the companion for details: “Benötigen Sie während des Spiels mehr Informationen, so schlagen Sie unter dem jeweiligen Stichwort (➔) im CATAN-Almanach nach.” (`CATAN22-RULES`, PDF p. 2). Both assigned PDFs have the same 2022 copyright, article number, and matching InDesign production stem.

Archived but **not assigned**:

- `game_almanac_base_2015.pdf`, SHA-256 `9d8d0607326f82ea7bfda11aafa5be65aaffe41f043ae996f6d72f30e92c049f` (“Regelstand: Januar 2015” despite its download label).
- `game_almanac_bigbox_2016.pdf`, SHA-256 `0dd37693be9d898752136f6a032f224580782d7c3e79dda37fed1e0b321577a2` (Big Box edition).

## Clear facts

### Components and fixed beginner setup

- **CAT-INV-01 (`clear`, `CATAN22-ALMANAC`, p. 23):** “19 Landfelder” comprise 4 forest, 4 pasture, 4 fields, 3 hills, 3 mountains, and 1 desert. There are 6 frame pieces with 9 harbors and 18 number tokens: one each of 2 and 12, and two each of 3, 4, 5, 6, 8, 9, 10, and 11.
- **CAT-INV-02 (`clear`, `CATAN22-ALMANAC`, p. 23):** “95 Rohstoffkarten (je 19)” means exactly 19 each of wood, brick, wool, grain, and ore.
- **CAT-INV-03 (`clear`, `CATAN22-ALMANAC`, pp. 6, 23):** The 25 development cards are 14 Knights, 6 progress cards, and 5 victory-point cards. The progress deck contains two each of Road Building, Year of Plenty/“Erfindung,” and Monopoly. The five one-point cards are Library, Marketplace, City Hall, Chapel, and University.
- **CAT-INV-04 (`clear`, `CATAN22-ALMANAC`, p. 23):** Each color has 15 roads, 5 settlements, and 4 cities; the box also has one robber, two dice, four building-cost cards, and the two special cards Longest Road and Largest Army.
- **CAT-SETUP-01 (`clear`, `CATAN22-RULES`, pp. 1–2):** Four-player beginner play uses the exact illustrated p. 1 arrangement. “Jeder Spieler platziert 2 Straßen und 2 Siedlungen … gemäß der Abbildung auf Seite 1.” The canonical source transcription is frozen in `environment_profile.json` as 19 hexes (`h00`–`h18`), 54 vertices (`v00`–`v53`), and 72 edges.
- **CAT-SETUP-02 (`clear`, `CATAN22-RULES`, p. 1):** Row-major terrains/numbers are: `ore10,wool2,wood9 / grain12,brick6,wool4,brick10 / grain9,wood11,desert,wood3,ore8 / wood8,ore3,grain4,wool5 / brick5,grain6,wool11`. The robber starts on the central desert.
- **CAT-SETUP-03 (`clear`, `CATAN22-RULES`, pp. 1–2):** Starting resources come only from each lettered settlement: red A gets 2 wood + 1 grain; blue B gets wood + brick + ore; orange C gets 2 grain + ore; white D gets wood + wool + ore. Therefore the bank starts with wood 15, brick 18, wool 18, grain 16, and ore 16.
- **CAT-SETUP-04 (`clear`, `CATAN22-RULES`, p. 2):** Resource cards are sorted into five open stacks; development cards are shuffled into a face-down deck. The oldest player starts and turns then pass left.

### Turn order, production, and phase boundaries

- **CAT-TURN-01 (`clear`, `CATAN22-RULES`, p. 2):** In the stated order, the active player must roll, may trade, and may build: “1. Er muss … auswürfeln … 2. Er kann handeln … 3. Er kann bauen.”
- **CAT-TURN-02 (`clear`, `CATAN22-ALMANAC`, p. 6):** Under the assigned strict phases, “Nach dem ‘Bauen’ ist der Zug des Spielers beendet”; trading cannot resume after building. The Almanach’s merged trade/build rule on p. 7 is expressly a recommendation for experienced players and is excluded.
- **CAT-TURN-03 (`clear`, `CATAN22-RULES`, p. 2; `CATAN22-ALMANAC`, p. 6):** One eligible Knight or progress card may be played at any stable point of the active turn, including before rolling. A card bought that turn cannot be played, except a newly bought victory-point card may establish an immediate win.
- **CAT-PROD-01 (`clear`, `CATAN22-RULES`, p. 2):** For a non-seven roll, every adjacent settlement on each matching unblocked land hex receives one matching resource; every adjacent city receives two. Multiple entitlements add.
- **CAT-PROD-02 (`clear`, `CATAN22-RULES`, p. 4; `CATAN22-ALMANAC`, p. 11):** The desert never produces. A robber-occupied hex produces nothing for any adjacent building while the robber remains there.

### Trade and harbors

- **CAT-TRADE-01 (`clear`, `CATAN22-RULES`, p. 3; `CATAN22-ALMANAC`, p. 6):** Only the active player trades. Terms and positive quantities are freely negotiated; non-active players cannot trade directly with one another. “Das Verschenken von Karten ist nicht erlaubt (Tausch von 0 gegen 1 oder mehr Karten).” Only resource cards are supported trade objects.
- **CAT-TRADE-02 (`clear`, `CATAN22-RULES`, p. 3; `CATAN22-ALMANAC`, p. 9):** Maritime rates are 4 identical resources for 1 different resource without a harbor, 3:1 at a generic harbor, and 2:1 of the pictured resource at a special harbor.
- **CAT-TRADE-03 (`clear`, `CATAN22-ALMANAC`, p. 7):** A harbor settlement built after the strict trade phase cannot be used until the next turn’s trade phase: “Ein soeben errichteter Hafen kann erst in der nächsten Runde … benutzt werden.”
- **CAT-TRADE-04 (`clear`, `CATAN22-ALMANAC`, p. 9):** Harbor access explicitly belongs to a “Siedlung (oder Stadt)” at that harbor location.

### Building and board graph

- **CAT-BUILD-01 (`clear`, `CATAN22-RULES`, pp. 3–4):** Costs are road = wood + brick; settlement = wood + brick + wool + grain; city = 3 ore + 2 grain; development card = ore + wool + grain.
- **CAT-BUILD-02 (`clear`, `CATAN22-RULES`, pp. 3–4):** A road occupies one empty edge and must connect to the player’s road, settlement, or city without crossing an opponent building at the connecting vertex. A settlement requires an own road and all three neighboring vertices must be building-free. A city only replaces an own settlement.
- **CAT-BUILD-03 (`clear`, `CATAN22-ALMANAC`, pp. 6, 10):** Building is limited by physical stock. A settlement returned by a city upgrade re-enters that player’s available stock and may be built again later.
- **CAT-ROAD-01 (`clear`, `CATAN22-RULES`, p. 3):** The first continuous road of at least five edges gains Longest Road and 2 points; branches are not summed. A strictly longer road takes the card immediately. An opponent building interrupts a route.
- **CAT-ROAD-02 (`clear`, `CATAN22-ALMANAC`, p. 8):** An own building does not interrupt an own road. On recalculation, a tied current holder retains the card; a leading tie not including the former holder sets the card aside; it is also set aside if no route remains at least five.

### Seven, robber, and development cards

- **CAT-ROBBER-01 (`clear`, `CATAN22-RULES`, p. 4):** A seven produces nothing. Every player with more than seven resource cards discards floor(hand size / 2); development cards do not count.
- **CAT-ROBBER-02 (`clear`, `CATAN22-RULES`, p. 4):** After the discards, the active player must move the robber to a different land hex. A later matching roll produces nothing on that hex.
- **CAT-ROBBER-03 (`clear`, `CATAN22-ALMANAC`, pp. 8–9):** If multiple opponents have buildings adjacent to the destination, the mover chooses whom to rob. Only one resource card, never a development card, can transfer. A Knight moves the robber but does not cause seven-discard checks.
- **CAT-DEV-01 (`clear`, `CATAN22-ALMANAC`, p. 6):** Road Building places two free roads subject to normal road rules. Year of Plenty takes any two resources from the bank, including two of the same type. Monopoly transfers every opponent-held card of one chosen resource; a player with none transfers nothing.
- **CAT-DEV-02 (`clear`, `CATAN22-RULES`, p. 4):** Played progress cards leave the game. Played Knights remain face-up and count toward Largest Army.
- **CAT-ARMY-01 (`clear`, `CATAN22-RULES`, p. 4):** The first player with three face-up Knights receives Largest Army and 2 points. It transfers only when another player has strictly more face-up Knights.

### Information, scoring, and terminal timing

- **CAT-INFO-01 (`clear`, `CATAN22-RULES`, p. 2; `CATAN22-ALMANAC`, p. 6):** Resource identities in another player’s hand and unplayed development-card identities are private. Development cards stay secret until use; victory-point cards remain concealed until they establish victory.
- **CAT-INFO-02 (`clear`, `CATAN22-ALMANAC`, p. 10):** Face-down development-card counts are physically visible: the Almanach discusses a player having “1 oder 2 verdeckte Karten” in front of them. Played Knights and other played cards are public.
- **CAT-SCORE-01 (`clear`, `CATAN22-ALMANAC`, p. 10):** Settlement = 1 point, city = 2, each special card = 2, each victory-point development card = 1.
- **CAT-WIN-01 (`clear`, `CATAN22-RULES`, p. 4; `CATAN22-ALMANAC`, p. 10):** Only the active player can win. If that player has or reaches at least ten points, “so beendet er sofort das Spiel und gewinnt.” A non-active player at ten does not win until becoming active and still possessing ten.

## Approved human decisions (2026-07-23)

1. **CAT-D-SCOPE (`human_decision`):** Use exactly four players, the illustrated beginner setup, and strict roll → trade → build. **Rationale:** isolates one source-supported game condition and excludes the optional experienced-player phase merge.
2. **CAT-D-WIN (`human_decision`):** Check victory after every completed atomic action or committed subaction; if the active player then has at least ten, terminate immediately. This includes turn start before rolling and the first free road of Road Building. **Rationale:** gives full effect to “sofort.”
3. **CAT-D-ROBBER (`human_decision`):** If at least one adjacent opponent holds resources, the mover must choose one such opponent and steal uniformly from that resource multiset. Empty opponents are ineligible; if none is eligible, movement finishes without theft. **Rationale:** reconciles mandatory “raubt” in the primary with permissive “darf” and the missing empty-hand procedure in the Almanach.
4. **CAT-D-PORT-CITY (`human_decision`):** A city retains its harbor. **Rationale:** the matching Almanach expressly says “Siedlung (oder Stadt)” (p. 9), and the city replaces the settlement at the same vertex.
5. **CAT-D-ROAD-CARD (`human_decision`):** Road Building places the maximum feasible number up to two, sequentially. If two are legal and available, both are required; otherwise place exactly the feasible number. Re-evaluate legality and victory after each road. **Rationale:** preserves the printed two-road effect without inventing an impossible placement.
6. **CAT-D-LONGEST (`human_decision`):** Longest Road is the maximum edge-simple trail: no road edge may be counted twice, but a vertex may be revisited when a trail permits it. Opponent-occupied vertices terminate traversal. **Rationale:** formalizes “durchgehender Straßenzug (Abzweigungen zählen nicht)” for loops and figure-eight graphs.
7. **CAT-D-TRADE (`human_decision`):** One committed domestic trade may contain several positive bilateral legs, each directly between the active player and one partner. No transfer may run directly between two non-active players. The canonical interface builds the offer one resource at a time in a finite `trade_offer` subphase, then commits every leg atomically or cancels without transfer. **Rationale:** models the user-approved multilateral agreement, avoids exponential legal-action enumeration, and preserves “immer nur mit dem Spieler … der an der Reihe ist.”
8. **CAT-D-VP-REVEAL (`human_decision`):** Victory detection automatically reveals, in development-hand order, only the minimum number of hidden victory-point cards needed to establish ten; this does not consume the one Knight/progress-card allowance.
9. **CAT-D-DISCARD (`human_decision`):** Seven discards are privately committed and applied together. Public data exposes required quantities, completion status, and resulting aggregate open bank counts, not each player’s resource identities.
10. **CAT-D-OBS (`human_decision`, interface):** Public observations expose every resource-hand size, face-down development-card count, bank resource count, development-deck size, board state, played cards, and public score. They hide opponents’ resource/development identities and hidden victory points. **Rationale:** development counts and open bank piles are source-visible; resource hand-size publicity is not stated and is therefore recorded as a contract convention rather than scored publisher fact.

## Explicit non-rule interface decisions

- Canonical seats are red, blue, orange, white; seat 0 represents the oldest player and starts. The source says “oldest,” not a color.
- Constructor seeds deterministically control dice, development shuffle, and random theft. Scripted chance queues are evaluator-only fixture data.
- Invalid actions are validated before mutation and rejected atomically.
- The fixed p. 1 graphic is transcribed into canonical IDs in `environment_profile.json`. Hard setup cases check the terrain/number layout, pieces, starting hands, harbor inventory, and clockwise harbor-type sequence; exact drawn dock-to-vertex artwork is retained in the profile but not scored independently.

## Visible but unscored source gaps

- **CAT-GAP-SHORTAGE (`not_testable`):** Neither source defines production allocation when a resource bank pile cannot satisfy all entitlements, nor partial/failure behavior for Year of Plenty or a requested bank trade when stock is insufficient. All such states remain unscored.
- **CAT-GAP-RANDOM (`not_testable` as a publisher rule):** The sources require dice, a shuffled deck, and a blind theft but specify no software RNG algorithm. Only seed reproducibility and transfer invariants are interface-tested.
- **CAT-GAP-DISCARD-VIS (`human_decision`, not publisher-scored):** Exact discard order and player-specific identity disclosure are absent; `CAT-D-DISCARD` is evaluated only in the human-decision evidence group.
- **CAT-GAP-HAND-COUNT (`human_decision`, not publisher-scored):** The sources do not expressly classify resource hand size as public or private; `CAT-D-OBS` is an interface convention.

No unresolved material assumption remains for the frozen condition. Corrections update the current facts/profile/suite while Git and recorded hashes preserve prior runs.
