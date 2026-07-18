# Bohnanza rule analysis

## Sources

- **RULES** — `game_rules.pdf`; role: `publisher_rulebook`; 11 PDF pages.
- **COMPONENTS** — `game_components.pdf`; role: `user_observation`; 3 PDF pages. Used as inventory/setup evidence only, not as an independent gameplay authority.

## Atomic facts

### Inventory and setup

1. **Base-game player count and field mats**
   - Source/page: **RULES, PDF p.2**
   - Quote: “**GRUNDSPIEL (3–5 SPIELER)**”
   - Quote: “**Nehmt euch je eine der Bohnenfeld-Ablagen. Die Ablagen haben eine Seite mit drei Bohnenfeldern und eine Seite mit zwei Bohnenfeldern.**”
   - Preconditions: Base game setup.
   - Action/result: Each of 3–5 players receives one double-sided field mat.
   - Interpretation: Required mat count equals player count; each mat has a two-field and three-field side.
   - Status: **clear**

2. **Initial field count by player count**
   - Source/page: **RULES, PDF p.2**
   - Quote: “**Spielt ihr zu dritt, legt jeder die Seite mit den drei Bohnenfeldern vor sich ab. Spielt ihr zu viert oder zu fünft, legt jeder die Seite mit den zwei Bohnenfeldern vor sich ab.**”
   - Preconditions: Setup.
   - Action/result: Three players start with three fields each; four or five players start with two.
   - Status: **clear**

3. **Start-player and overview cards**
   - Source/page: **RULES, PDF p.2**
   - Quote: “**Bestimmt einen Startspieler. Er erhält die Startspielerkarte. Für jeden Spieler gibt es außerdem eine Übersichtskarte mit den einzelnen Phasen des Spiels.**”
   - Preconditions: Setup.
   - Action/result: One chosen player receives the start-player card; each player has a phase overview card.
   - Interpretation: One start-player card is required. Exact packaged number of overview cards is not stated, only one per supported player.
   - Status: **clear** for setup; **not specified** for exact packaged overview-card count.

4. **Exact base-deck total and per-type counts**
   - Source/page: **RULES, PDF p.2**
   - Quote: “**Es gibt 104 Karten mit acht verschiedenen Bohnensorten. Wie oft eine Sorte im Spiel vertreten ist, zeigt euch die große Zahl auf der jeweiligen Bohnenkarte.**”
   - The page’s illustrated counts identify:
     - Gartenbohne: **6**
     - Rote Bohne: **8**
     - Augenbohne: **10**
     - Sojabohne: **12**
     - Brechbohne: **14**
     - Saubohne: **16**
     - Feuerbohne: **18**
     - Blaue Bohne: **20**
   - Interpretation: 6+8+10+12+14+16+18+20 = **104 cards**.
   - Status: **clear**

5. **Variant-only bean types**
   - Source/page: **RULES, PDF p.2**
   - Quote: “**Hinweis: Kakao-, Weinbrand- und Kaffeebohnen sowie Acker- und Elsterbohnen werden nur in den Varianten verwendet (siehe ab Seite 10).**”
   - Preconditions: Base game.
   - Result: These types are excluded from the ordinary base game and appear only in variants.
   - Status: **clear**

6. **Ackerbohnen-variant deck composition**
   - Source/page: **RULES, PDF p.10**
   - Quote: “**Die Ackerbohnen könnt ihr im Spiel mit vier oder fünf Spielern einsetzen. Nehmt hierfür alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen.**”
   - Preconditions: Ackerbohnen variant, 4–5 players.
   - Action/result: Use every base-game type plus Ackerbohnen and Weinbrandbohnen.
   - Status: **clear** for included types; RULES does not state their added card counts here.

7. **Exact Ackerbohnen-variant total**
   - Source/page: **COMPONENTS, PDF p.1**
   - Quote: “**Verwendet genau 129 Bohnenkarten: 104 aus dem Grundspiel, 22 Weinbrandbohnen und 3 Ackerbohnen.**”
   - Preconditions: Inventory check for the 4–5-player Ackerbohnen variant.
   - Result: 104 + 22 + 3 = **129 bean cards**.
   - Status: **clear** as user-observed inventory evidence.

8. **Exact complete variant per-type inventory**
   - Source/page: **COMPONENTS, PDF pp.2–3**
   - Quote: “**Summe: 129 Bohnenkarten.**”
   - Listed quantities:
     - Weinbrandbohne: **22**
     - Blaue Bohne: **20**
     - Feuerbohne: **18**
     - Saubohne: **16**
     - Brechbohne: **14**
     - Sojabohne: **12**
     - Augenbohne: **10**
     - Rote Bohne: **8**
     - Gartenbohne: **6**
     - Ackerbohne: **3**
   - Interpretation: Exact deck inventory for the documented variant.
   - Status: **clear** as user-observed inventory evidence.

9. **Explicit excluded cards**
   - Source/page: **COMPONENTS, PDF p.3**
   - Quote: “**Nicht in diesem Kartensatz liegen**”
   - Quote: “**24 Kaffeebohnen**”; “**4 Kakaobohnen**”; “**39 Auftragskarten**”; “**Elsterbohnen, AMIGO-Bohnentaler oder Karten anderer Bohnanza-Ausgaben**”
   - Preconditions: Checking the 129-card Ackerbohnen-variant deck.
   - Result: These materials are excluded.
   - Status: **clear** as user-observed inventory evidence.

10. **Remaining physical-material quantities**
    - Sources/pages: **RULES, PDF pp.2–3**
    - Quotes: “**Nehmt euch je eine der Bohnenfeld-Ablagen.**”; “**Er erhält die Startspielerkarte.**”; “**Für jeden Spieler gibt es außerdem eine Übersichtskarte**”
    - Interpretation: Setup requires one field mat per player, one start-player card, and one overview card per player. Neither source supplies a complete exact package inventory for these non-bean-card materials.
    - Status: **not specified**

### Hands and private information

11. **Initial hands**
    - Source/page: **RULES, PDF p.3**
    - Quote: “**Mischt alle Karten und verteilt an jeden Spieler einzeln fünf Handkarten.**”
    - Preconditions: Setup.
    - Action/result: Shuffle all participating cards and deal five individual hand cards to every player.
    - Status: **clear**

12. **Immutable hand order**
    - Source/page: **RULES, PDF p.3**
    - Quote: “**Die Reihenfolge der Karten auf deiner Hand darfst du während des gesamten Spiels nicht ändern. Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar. Jede weitere steckst du dahinter. Du darfst die Karten nicht sortieren.**”
    - Preconditions: Cards are in a player’s hand.
    - Action/result: Hand order never changes by player choice; earliest dealt card is front and fully visible; later cards go behind it.
    - Interpretation: The front card is public. Whether every non-front card’s identity must be hidden from other players is not expressly stated.
    - Status: **clear** on ordering; **ambiguous** on the complete visibility model.

13. **Draw pile orientation**
    - Source/page: **RULES, PDF p.3**
    - Quote: “**Legt die restlichen Karten mit der Talerseite nach oben als Nachziehstapel in die Tischmitte.**”
    - Result: Remaining cards form the central draw pile with coin sides upward.
    - Status: **clear**

### Turn order and phases

14. **Active-player order**
    - Source/page: **RULES, PDF p.4**
    - Quote: “**Der Startspieler ist der erste aktive Spieler. Danach geht es im Uhrzeigersinn weiter.**”
    - Quote: “**Die Startspielerkarte wird nicht weitergegeben.**”
    - Result: Turns proceed clockwise from the start player; the marker remains with its original holder.
    - Status: **clear**

15. **Four turn phases**
    - Source/page: **RULES, PDF p.4**
    - Quote: “**Als aktiver Spieler führst du nacheinander vier Phasen durch:**”
    - Quote: “**1. Bohnenkarten von der Hand anbauen / 2. Bohnenkarten aufdecken und handeln / 3. Gehandelte und aufgedeckte Bohnenkarten anbauen / 4. Bohnenkarten nachziehen**”
    - Result: Phases occur in this order.
    - Status: **clear**

16. **Field type restriction**
    - Source/page: **RULES, PDF p.4**
    - Quote: “**Auf einem Feld darfst du nur Bohnen der gleichen Sorte anbauen. Es ist dir aber erlaubt, dieselbe Sorte auf mehreren Feldern zur gleichen Zeit anzubauen. Die Bohnenkarten werden untereinander auf die Felder gelegt.**”
    - Result: Each field contains one type, but the same type may occupy multiple fields.
    - Status: **clear**

### Phase 1: planting from hand

17. **Mandatory first planting**
    - Source/page: **RULES, PDF p.4**
    - Quote: “**Du musst die vorderste Bohnenkarte, also die ganz sichtbare Karte, aus deiner Hand auf einem deiner Felder anbauen.**”
    - Preconditions: Player has at least one hand card.
    - Action/result: Plant the front card.
    - Status: **clear**

18. **Optional second planting; no third**
    - Source/page: **RULES, PDF p.4**
    - Quote: “**Danach darfst du eine weitere Bohnenkarte, die nun ganz sichtbare Karte, auf einem deiner Felder anbauen. Eine dritte Bohne darfst du nicht anbauen.**”
    - Result: The new front card may be planted; no third hand card may be planted in this phase.
    - Status: **clear**

19. **Forced harvest to make planting legal**
    - Source/page: **RULES, PDF p.5**
    - Quote: “**Musst du eine Bohnensorte anbauen, hast aber kein Feld dafür zur Verfügung, musst du zuerst ein Feld abernten**”
    - Preconditions: A mandatory card cannot fit any field.
    - Action/result: Harvest a field before planting.
    - Status: **clear**

20. **Empty-hand Phase 1**
    - Source/page: **RULES, PDF p.5**
    - Quote: “**Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.**”
    - Result: Skip Phase 1 when the hand is empty at its start.
    - Status: **clear**

### Phase 2: reveal and trade

21. **Reveal two cards**
    - Source/page: **RULES, PDF p.5**
    - Quote: “**Ziehe die obersten zwei Karten vom Nachziehstapel und lege sie für alle sichtbar aufgedeckt daneben.**”
    - Result: Active player reveals the top two draw-pile cards publicly.
    - Status: **clear**

22. **Ownership and permitted disposition of reveals**
    - Source/page: **RULES, PDF p.5**
    - Quote: “**Die aufgedeckten Karten gehören dir. Sie stehen dir zum Anbau auf deinen Feldern oder zum Handel mit deinen Mitspielern zur Verfügung.**”
    - Result: Revealed cards belong to the active player and may be planted or traded.
    - Status: **clear**

23. **Only active player may trade**
    - Source/page: **RULES, PDF p.5**
    - Quote: “**Nur du als aktiver Spieler darfst mit anderen Spielern handeln. Deine Mitspieler dürfen untereinander nicht handeln.**”
    - Result: Every trade includes the active player; inactive players cannot trade with each other.
    - Status: **clear**

24. **Tradable cards**
    - Source/page: **RULES, PDF p.5**
    - Quotes: “**Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.**”
    - “**Als aktiver Spieler darfst du auch mit den zwei aufgedeckten Karten handeln.**”
    - Result: Any hand card may be offered; active player may additionally trade either reveal.
    - Status: **clear**

25. **No retrading or field-card trading**
    - Source/page: **RULES, PDF p.5**
    - Quotes: “**Mit Karten, die ihr nach einem Handel bekommt, dürft ihr nicht weiterhandeln.**”
    - “**Mit Karten, die auf Feldern liegen, dürft ihr ebenfalls nicht handeln.**”
    - Result: Received cards and planted cards cannot be traded.
    - Status: **clear**

26. **Unequal exchanges**
    - Source/page: **RULES, PDF p.5**
    - Quote: “**Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.**”
    - Result: Trade sides need not contain equal numbers of cards.
    - Status: **clear**

27. **Agreement before removing a hand card**
    - Source/page: **RULES, PDF p.6**
    - Quote: “**Ziehe eine Karte erst aus der Hand, sobald der Handel auch wirklich zustande kommt. Denn beide Spieler müssen dem Handel zustimmen.**”
    - Result: A trade requires both parties’ consent; hand cards remain in hand until agreement.
    - Status: **clear**

28. **Received cards remain outside the hand**
    - Source/page: **RULES, PDF p.6**
    - Quote: “**Bohnenkarten, die du nach einem Handel erhältst, legst du zunächst quer neben deinen Feldern ab. Auf die Hand nehmen darfst du sie nicht.**”
    - Result: Received cards wait face-up/outside the ordered hand for Phase 3.
    - Status: **clear**

29. **Gifts require acceptance**
    - Source/page: **RULES, PDF p.6**
    - Quote: “**Als besondere Form des Handelns dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen. Lehnt er ab, kommt der Handel nicht zustande.**”
    - Result: Zero-card consideration is allowed, but recipient consent is mandatory.
    - Status: **clear**

30. **Ending trade phase**
    - Source/page: **RULES, PDF p.6**
    - Quote: “**Erst wenn du nicht mehr handeln möchtest, sagst du es deinen Mitspielern und beendest diese Phase.**”
    - Result: Active player declares the phase ended.
    - Status: **clear**

### Phase 3: mandatory planting

31. **Plant every traded card**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Alle Spieler, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen.**”
    - Result: Every player must plant all cards received in trades.
    - Status: **clear**

32. **Plant every untraded reveal**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Als aktiver Spieler musst du auch jede aufgedeckte Karte anbauen, die du nicht gehandelt hast.**”
    - Result: Active player must plant each remaining revealed card.
    - Status: **clear**

33. **Planting order is chosen individually**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.**”
    - Result: Each affected player chooses the order of their new cards, which may affect forced harvests.
    - Status: **clear**

34. **Forced harvest during Phase 3**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Solltest du eine Bohnenkarte anbauen müssen, die zu keiner Sorte auf deinen Feldern passt, musst du zuerst ein Feld abernten, bevor du weiter anbauen darfst.**”
    - Result: Harvest before continuing when a mandatory card does not fit.
    - Status: **clear**

### Phase 4 and draw-pile recycling

35. **Base-game draw**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Ziehe als aktiver Spieler nacheinander drei Karten vom Nachziehstapel. Stecke sie, ohne die Reihenfolge zu ändern, hinter deine letzte Handkarte.**”
    - Result: Active player draws three sequentially and appends them in draw order.
    - Status: **clear**

36. **Turn transition**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Danach ist dein linker Mitspieler der neue aktive Spieler.**”
    - Result: After drawing, the player to the left becomes active.
    - Status: **clear**

37. **Recycling the discard pile**
    - Source/page: **RULES, PDF p.9**
    - Quote: “**Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels. Lege sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.**”
    - Result: When the last draw-pile card is drawn, shuffle the discard pile into a new face-down draw pile.
    - Status: **clear**
    - Residual issue: The source does not explicitly state how to complete a multi-card draw if insufficient cards remain and the discard pile is empty.

38. **Variant Phase 4**
    - Source/page: **RULES, PDF p.10**
    - Quote: “**Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.**”
    - Preconditions: “Drei neue Bohnensorten” flow, which the Ackerbohnen variant adopts.
    - Result: Each player draws one card, active player first, then clockwise.
    - Status: **clear**

### Harvesting and scoring

39. **Harvest timing**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.**”
    - Result: A player may harvest their own fields at any time, including during another player’s turn.
    - Status: **ambiguous**
    - Reason: “jederzeit” does not define interruption/priority boundaries or whether harvesting may occur inside another atomic action.

40. **Normal harvest conversion**
    - Source/page: **RULES, PDF p.8**
    - Quote: “**Zähle alle Karten auf dem Bohnenfeld, das du abernten möchtest. Schaue auf das Bohnometer der obersten Karte. Drehe so viele Karten, wie du laut Bohnometer an Bohnentaler bekommst, auf die Talerseite. Lege diese Karten auf deinen Talerstapel. Die restlichen Karten des abgeernteten Feldes legst du offen auf den Ablagestapel. Nach einer Ernte ist das abgeerntete Feld immer leer.**”
    - Result: Award the meter’s coin count by flipping that many harvested bean cards to coin side; discard the rest; field becomes empty.
    - Status: **clear**

41. **Zero-value harvests**
    - Source/page: **RULES, PDF p.7**
    - Quote: “**Beachte: Bei manchen Ernten erhältst du keine Taler.**”
    - Result: A legal harvest can yield zero coins.
    - Status: **clear**

42. **Bean-protection rule**
    - Source/page: **RULES, PDF p.8**
    - Quote: “**Du darfst auf einem Feld keine einzelne Bohnenkarte ernten, wenn auf mindestens einem deiner Felder mehr als eine Bohnenkarte liegt.**”
    - Preconditions: Player wishes to harvest a one-card field.
    - Result: Illegal if any of that player’s fields contains more than one card.
    - Interpretation: If every occupied field has at most one card, a singleton field may be harvested.
    - Status: **clear**

43. **Ackerbohne special harvest**
    - Source/page: **RULES, PDF p.11**
    - Quote: “**Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld. Drehe dazu deine Bohnenfeld-Ablage auf die Seite mit drei Bohnenfeldern.**”
    - Result: Harvesting exactly two Ackerbohnen unlocks the third field by flipping the mat.
    - Status: **clear**

44. **Handling existing beans when mat flips**
    - Source/page: **RULES, PDF p.11**
    - Quote: “**Hast du auf deinem ersten oder zweiten Feld in dem Moment noch weitere Bohnen liegen, legst du diese nach dem Umdrehen entsprechend auf das erste oder zweite Feld der Bohnenfeld-Ablage zurück.**”
    - Result: Existing first/second field crops persist in corresponding positions.
    - Status: **clear**

45. **Repeated two-Ackerbohnen harvest**
    - Source/page: **RULES, PDF p.11**
    - Quote: “**Hast du bereits ein drittes Bohnenfeld, erhältst du für das Ernten von zwei Ackerbohnen nichts.**”
    - Result: If the third field is already unlocked, two Ackerbohnen yield nothing.
    - Status: **clear**

46. **Three-Ackerbohnen harvest**
    - Source/page: **RULES, PDF p.11**
    - Quote: “**Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.**”
    - Result: Three Ackerbohnen yield three coins, rather than unlocking a field.
    - Status: **clear**

### Ending, elimination, and winner

47. **Base-game terminal trigger**
    - Source/page: **RULES, PDF p.9**
    - Quote: “**Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.**”
    - Result: Third depletion triggers game end.
    - Status: **clear**

48. **Finishing phases after terminal trigger**
    - Source/page: **RULES, PDF p.9**
    - Quote: “**Sollte dies beim Aufdecken der Karten in der 2. Phase ‚Bohnenkarten aufdecken und handeln‘ passieren (auch wenn nur eine Karte aufgedeckt werden konnte), spielt ihr die 2. und die 3. Phase noch zu Ende.**”
    - Result: If depletion occurs during Phase 2 revealing, complete Phases 2 and 3.
    - Status: **clear**
    - Residual issue: The rule does not expressly describe terminal handling if depletion occurs during Phase 4 or variant per-player drawing.

49. **Final harvest and score**
    - Source/page: **RULES, PDF p.9**
    - Quote: “**Alle Spieler ernten noch ihre Bohnenfelder und erhalten gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr. Jeder zählt die Taler in seinem Talerstapel. Jede Karte ist einen Taler wert. Wer die meisten Taler besitzt, gewinnt.**”
    - Result: Harvest all fields, ignore hands, count one point per coin card; highest score wins.
    - Status: **clear**

50. **Tie-break**
    - Source/page: **RULES, PDF p.9**
    - Quote: “**Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.**”
    - Result: Among tied players, the one furthest clockwise from the original start player wins.
    - Status: **clear**

51. **Variant terminal trigger**
    - Source/page: **RULES, PDF p.10**
    - Quote: “**Das Spiel zu dritt endet, sobald der Nachziehstapel zum zweiten Mal leer wird. Bei vier oder mehr Spielern endet das Spiel wie gewohnt, sobald der Nachziehstapel zum dritten Mal leer wird.**”
    - Preconditions: Variant using the stated altered Phase 4.
    - Result: Two depletions at 3 players; three at 4+ players.
    - Status: **clear**
    - For the Ackerbohnen variant specifically, only 4–5 players are permitted, so the three-depletion rule applies.

52. **Elimination**
    - Sources/pages: **RULES and COMPONENTS, all reviewed pages**
    - Direct quote: No elimination rule appears.
    - Interpretation: Neither source specifies player elimination.
    - Status: **not specified**

## Cross-source comparison and apparent conflicts

### No direct inventory conflict found

- **RULES, PDF p.2:** “**Es gibt 104 Karten mit acht verschiedenen Bohnensorten.**”
- **COMPONENTS, PDF p.1:** “**Verwendet genau 129 Bohnenkarten: 104 aus dem Grundspiel, 22 Weinbrandbohnen und 3 Ackerbohnen.**”
- Assessment: **Not a conflict.** RULES describes the base deck; COMPONENTS describes the expanded Ackerbohnen-variant deck and preserves all 104 base cards.

- **RULES, PDF p.10:** “**Nehmt hierfür alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen.**”
- **COMPONENTS, PDF p.1:** “**104 aus dem Grundspiel, 22 Weinbrandbohnen und 3 Ackerbohnen.**”
- Assessment: **Consistent.** COMPONENTS adds observed quantities absent from the rulebook.

### Apparent gameplay-scope conflict inside COMPONENTS

- **COMPONENTS, PDF p.1:** “**Diese Datei ist eine neu formulierte, inoffizielle Spielhilfe.**”
- **COMPONENTS, PDF p.2:** “**1 Ackerbohne — 0 Taler — Normale Null-Ernte; die Bohnenschutzregel kann die Ernte verbieten.**”
- **RULES, PDF p.11:** describes only the special outcomes for harvesting two or three Ackerbohnen and does not expressly state the one-card outcome.
- Why apparent conflict matters: COMPONENTS supplies a gameplay consequence not directly stated in RULES. It is not necessarily contradictory, but under its `user_observation` role it must not silently establish that rule.
- Classification: **apparent source-scope conflict / RULES not specified**, not a textual contradiction.

### No other direct contradictions found

The per-type base counts, 129-card variant sum, Ackerbohne quantities, Ackerbohne rewards, and included/excluded type lists are mutually consistent across the reviewed pages.

## Material questions

1. **Private information:** Are identities of all hand cards behind the fully visible front card hidden from opponents, or may opponents inspect some/all of the ordered hand?
2. **Harvest timing:** What exact priority applies to “jederzeit” harvesting—may a player interrupt a draw, reveal, trade resolution, planting sequence, or another player’s declared action?
3. **Empty-pile transition:** During a required multi-card draw/reveal, if the pile empties and the discard pile is empty or contains too few cards, how is the action completed?
4. **Terminal transition:** If the final required depletion occurs during base Phase 4 or during variant clockwise per-player drawing, which remaining draws/phases/turn steps are completed?
5. **One Ackerbohne:** Is harvesting a singleton Ackerbohne a normal zero-coin harvest subject to the bean-protection rule? COMPONENTS says yes, but RULES does not expressly state it.
6. **Physical inventory:** What are the exact packaged counts of field mats and overview cards? RULES defines one per player but neither source gives a complete material manifest.
7. **Elimination:** Is elimination intentionally impossible? Neither supplied source states an elimination mechanism.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Returned inline atomic findings covering exact inventory, setup, legal actions, transitions, private information, elimination, terminal result, scoring, source comparison, and material questions with source IDs, PDF pages, German quotes, interpretations, and clarity classifications."
    }
  ],
  "changedFiles": [],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "Reviewed all fresh rendered pages for RULES (11 pages) and COMPONENTS (3 pages) using read-only image inspection",
      "result": "passed",
      "summary": "All supplied rendered pages were inspected; no web or remembered rules were used."
    }
  ],
  "validationOutput": [
    "Base counts sum to 104.",
    "Variant counts sum to 129: 104 base + 22 Weinbrandbohnen + 3 Ackerbohnen.",
    "No direct cross-source numerical contradiction found."
  ],
  "residualRisks": [
    "Exact non-card package quantities are not supplied.",
    "Some gameplay boundary conditions are absent from RULES.",
    "COMPONENTS contains gameplay summaries that cannot independently override or fill RULES gaps."
  ],
  "noStagedFiles": true,
  "diffSummary": "No files changed; findings returned inline as requested.",
  "reviewFindings": [
    "no blockers"
  ],
  "manualNotes": "COMPONENTS was treated only as user-observed inventory/setup evidence. Its gameplay statements were not silently promoted over RULES."
}
```

[38;2;136;136;136m✻ Turn took 2m 48s (Total time 5m 20s · 2 turns)[0m