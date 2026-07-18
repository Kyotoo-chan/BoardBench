# Independent edge review — Bohnanza

Source IDs:

- **RULES** — publisher rulebook, `game_rules.pdf`; citations use rendered PDF page plus printed page where visible.
- **COMPONENTS** — user-observation appendix, `game_components.pdf`; usable only for physical identification/inventory, not as authority for gameplay.

## Material questions

1. **Which experiment condition is intended: base game or the 4–5-player Ackerbohne variant?**
   The base game uses 104 cards and explicitly excludes variant beans: “**Es gibt 104 Karten mit acht verschiedenen Bohnensorten**” and “**Acker- und Elsterbohnen werden nur in den Varianten verwendet**” [RULES PDF p.1, printed p.3]. The Ackerbohne variant instead says to use all base-game varieties plus Ackerbohnen and Weinbrandbohnen [RULES PDF p.10: “**Nehmt hierfür alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen**”]. COMPONENTS inventories that variant as exactly 129 cards [COMPONENTS p.1: “**104 aus dem Grundspiel, 22 Weinbrandbohnen und 3 Ackerbohnen**”]. These are alternative setups, not one combined default.

2. **May COMPONENTS establish the hard exact inventory absent from RULES?**
   RULES establishes only the base total and the eight base multiplicities: 6, 8, 10, 12, 14, 16, 18, and 20, totaling 104 [RULES PDF p.1, printed p.3]. It does not state the number of Weinbrandbohnen or Ackerbohnen in the supplied publisher pages. COMPONENTS states “**Verwendet genau 129 Bohnenkarten: 104 aus dem Grundspiel, 22 Weinbrandbohnen und 3 Ackerbohnen**” [COMPONENTS p.1] and identifies the excluded components [COMPONENTS p.3: “**24 Kaffeebohnen … 4 Kakaobohnen … 39 Auftragskarten … Elsterbohnen, AMIGO-Bohnentaler**”]. Under the source-role boundary, this can support inventory identification but not independently establish gameplay effects.

3. **Does the Ackerbohne variant retain the normal five-card deal and ordinary four phases?**
   RULES says its flow corresponds to “Variante 1” [RULES PDF p.10: “**Der Spielablauf entspricht dem aus ‚Variante 1: Drei neue Bohnensorten‘**”]. The supplied preceding text says each player begins with five cards and performs the familiar four phases, but modifies phase 4 so every player draws one card, active player first clockwise [RULES PDF p.10: “**Jeder Spieler startet mit fünf Handkarten**”; “**zieht jeder von euch eine Karte … Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn**”]. A hard scenario should confirm that this cross-reference applies to Variant 2 rather than silently applying the base phase-4 rule of three cards to the active player [RULES PDF p.6, printed p.8: “**Ziehe als aktiver Spieler nacheinander drei Karten**”].

4. **What happens if fewer than two cards remain when phase 2 begins before the final exhaustion?**
   Phase 2 requires drawing the top two cards [RULES PDF p.4, printed p.6: “**Ziehe die obersten zwei Karten vom Nachziehstapel**”]. The exhaustion rule says that when the last card is drawn, shuffle the discard pile into a new deck [RULES PDF p.8, printed p.10: “**Ziehst du die letzte Karte … mische die Karten des Ablagestapels**”]. It does not explicitly say whether the second reveal is then drawn from the newly shuffled deck. The final-exhaustion clause expressly permits only one revealed card [RULES PDF p.8, printed p.10: “**auch wenn nur eine Karte aufgedeckt werden konnte**”], implying a special terminal case but not fully specifying the nonterminal continuation.

5. **What happens when exhaustion occurs partway through phase 4?**
   Base phase 4 requires three sequential draws [RULES PDF p.6, printed p.8: “**nacheinander drei Karten**”]. The game ends “**sobald der Nachziehstapel zum dritten Mal leer wird**” [RULES PDF p.8, printed p.10], but only exhaustion during phase 2 is granted explicit completion of phases 2 and 3. The source does not state whether remaining phase-4 draws are skipped, whether the turn ends immediately, or whether a newly created discard pile can be reshuffled.

6. **Can the discard pile be empty when a nonfinal exhaustion requires reshuffling?**
   RULES commands a shuffle of the discard pile upon drawing the last card [RULES PDF p.8, printed p.10], but does not specify behavior if that pile is empty. This can occur in a constructed state and should remain an unsupported-state question rather than receiving an invented recovery rule.

7. **May trades be multi-party, conditional, or deferred?**
   RULES establishes bilateral permissions and consent but gives no transaction grammar: only the active player trades with others, nonactive players cannot trade among themselves, unequal card counts are permitted, and both players must agree [RULES PDF pp.4–5, printed pp.6–7: “**Nur du als aktiver Spieler darfst mit anderen Spielern handeln**”; “**beide Spieler müssen dem Handel zustimmen**”; “**unterschiedlichen Kartenanzahl**”]. It does not resolve a single three-party bargain, promises contingent on another trade, or delayed delivery. Deterministic scenarios should restrict trades to immediate bilateral atomic exchanges.

8. **Is a zero-card exchange permitted, apart from an explicitly accepted gift?**
   Gifts are a special form of trade and require recipient consent [RULES PDF p.5, printed p.7: “**Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen**”]. The source does not define whether an empty-for-empty or request-only action is legal; only a gift with at least one offered card is sourced.

9. **Are other players entitled to inspect an entire hand?**
   RULES says the first dealt/front card is “**komplett sichtbar**,” later cards are placed behind it, and hand order may never change [RULES PDF p.2, printed p.4]. It also permits trading a hand card regardless of its position [RULES PDF p.4, printed p.6]. It does not expressly state whether the identities or order of covered cards are private, whether players may voluntarily reveal them, or whether public game state may expose them. An environment needs an approved observation model.

10. **When several mandatory phase-3 plantings conflict with limited fields, can a player harvest between each card and choose any planting order?**
    All sideways cards and the active player’s retained face-up cards must be planted, in an order chosen by that player [RULES PDF p.6, printed p.8: “**müssen diese nun anbauen**”; “**in welcher Reihenfolge**”]. If a card does not fit, a field must first be harvested [same page]. This supports harvesting between plantings, but the implementation should expose the order and harvest choices rather than choosing automatically.

11. **Does “harvest at any time” interrupt another player’s unresolved action?**
    RULES says “**Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist**” [RULES PDF p.6, printed p.8]. It does not define timing priority, simultaneous harvest ordering, or whether a nonactive player may interrupt an atomic trade or draw. An executable action boundary requires approval.

12. **How does the protection rule apply when every occupied field is a singleton or when empty fields exist?**
    The only prohibition is: “**Du darfst auf einem Feld keine einzelne Bohnenkarte ernten, wenn auf mindestens einem deiner Felder mehr als eine Bohnenkarte liegt**” [RULES PDF p.7, printed p.9]. Thus no cited prohibition applies when all occupied fields are singletons, but the source does not explicitly discuss choosing among them or counting empty fields. This should be tested narrowly from the stated condition.

13. **What exactly happens to two Ackerbohnen when the third field already exists?**
    RULES says two Ackerbohnen normally grant a third field, the harvested cards go to the discard pile, and “**Hast du bereits ein drittes Bohnenfeld, erhältst du für das Ernten von zwei Ackerbohnen nichts**” [RULES PDF p.11]. COMPONENTS says the same inventory aid outcome: “**Ist Feld 3 schon vorhanden: kein Ertrag**” and places both cards on the discard pile [COMPONENTS p.2]. “Nothing/no yield” could mean no field and no coins while ordinary harvest cleanup still occurs; that is strongly suggested but not stated in the same RULES sentence. Confirm before hard-coding.

14. **Does harvesting three Ackerbohnen grant coins but never unlock the third field?**
    RULES states “**Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler**” [RULES PDF p.11]. COMPONENTS adds “**Alle drei Karten werden zu Talern. Es wird kein drittes Feld freigeschaltet**” [COMPONENTS p.2]. The “no third field” gameplay conclusion is explicit only in the user-observation appendix; it should be treated as a question unless accepted as a physical reading of the card’s Bohnometer.

15. **COMPONENTS contains an internal Ackerbohne description conflict. Which inventory/card-face transcription is approved?**
    Its table correctly labels two Ackerbohnen as “**Drittes Bohnenfeld**” [COMPONENTS p.2], but its later detail heading says “**Bohnometer: 2 Karten = 2 | 3+ = 3 Taler**” before separately saying “**2 = Feld 3 | 3 = 3 Taler**” [COMPONENTS p.3]. RULES says two grant a third field, not two coins [RULES PDF p.11]. Because COMPONENTS is internally inconsistent and nonauthoritative for play, no scenario should expect two coins.

16. **COMPONENTS also conflicts with RULES over the base card example and likely shifted bean rows. Which values may be scored?**
    RULES explicitly gives Saubohne thresholds 3–4 = 1, 5–6 = 2, 7 = 3, 8+ = 4 [RULES PDF p.7, printed p.9: “**Für 3 oder 4 Saubohnen … einen Taler … 5 oder 6 … zwei … 7 … drei … 8 oder mehr … vier**”]. COMPONENTS p.2 assigns those thresholds to the row labelled Saubohne, but COMPONENTS p.3 says “**Saubohne … Bohnometer: 3 / 6 / 8 / 9**,” contradicting both its table and RULES. COMPONENTS p.3 also says Brechbohne is the official example, while RULES names Saubohne. Exact scoring expectations beyond directly readable publisher card faces should not be imported from COMPONENTS without approval.

17. **When exactly is final scoring initiated relative to voluntary harvest opportunities?**
    On the third exhaustion in phase 2, phases 2 and 3 finish, then all players harvest [RULES PDF p.8, printed p.10]. For exhaustion elsewhere, no continuation is specified. Since players may normally harvest at any time [RULES PDF p.6, printed p.8], the source does not say whether additional voluntary harvest actions are available after the terminal trigger but before compulsory final harvesting.

18. **Does the tiebreak include the start player, and how is “farthest clockwise” computed?**
    RULES says the tied winner is the player “**der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt**” [RULES PDF p.8, printed p.10], while the start-player card never moves [RULES PDF p.3, printed p.5]. For a tie including the start player, a deterministic interpretation likely compares clockwise seat distance, but the source supplies no explicit worked example.

## Candidate deterministic scenarios

1. **Base setup by player count**
   Given three players, each field board shows three fields; given four or five players, each shows two. Every player receives five cards one at a time; first dealt is frontmost; remaining deck is coin-side up [RULES PDF pp.1–2, printed pp.3–4].

2. **Base inventory**
   The active base deck has eight varieties with multiplicities 6, 8, 10, 12, 14, 16, 18, and 20, totaling 104; no Acker-, Weinbrand-, Kaffee-, Kakao-, or Elsterbohnen are included [RULES PDF p.1, printed p.3]. Use card identities from rendered faces rather than COMPONENTS scoring prose.

3. **Acker variant physical inventory, if approved as the selected condition**
   Four or five players; 104 base cards plus 22 Weinbrandbohnen plus 3 Ackerbohnen = 129; exclude coffee, cocoa, order, Elsterbohne, and separate coin cards [RULES PDF p.10; COMPONENTS pp.1, 3]. This tests inventory only; COMPONENTS does not govern play.

4. **Forced first planting**
   With cards in hand, phase 1 must plant the front card; exactly one additional now-front card may optionally be planted; a third may not be planted [RULES PDF p.3, printed p.5].

5. **Empty hand at phase-1 start**
   The active player performs no phase-1 planting and proceeds directly to phase 2 [RULES PDF p.4, printed p.6].

6. **Forced harvest to accommodate front card**
   If the mandatory front bean matches no field and no empty field exists, the player must choose and harvest a legally harvestable field before planting it [RULES PDF pp.3–4, printed pp.5–6], subject to the singleton protection rule [RULES PDF p.7, printed p.9].

7. **Field-type constraints**
   A field accepts only one bean variety; the same variety may simultaneously occupy multiple fields [RULES PDF p.3, printed p.5].

8. **Trading authority**
   During phase 2, only the active player may trade with each other player; two nonactive players cannot trade directly [RULES PDF p.4, printed p.6].

9. **Trading from arbitrary hand positions without reordering**
   A player may trade a card from any hand position. The card remains in hand until both sides consent; removing it then closes the gap without sorting the remaining cards [RULES PDF pp.4–5, printed pp.6–7].

10. **No retrading or field trading**
    A received card cannot be traded again, and cards planted on fields cannot be traded [RULES PDF p.4, printed p.6].

11. **Accepted and rejected gifts**
    An offered gift transfers only after recipient consent; rejection leaves ownership and locations unchanged [RULES PDF p.5, printed p.7].

12. **Received cards bypass the hand**
    Every traded or gifted card is placed sideways beside the recipient’s fields, never inserted into hand [RULES PDF p.5, printed p.7].

13. **Mandatory phase-3 planting and chosen order**
    Each player must plant every sideways card; active player also plants every untraded revealed card. Each affected player chooses their own planting order and may need to harvest between cards [RULES PDF p.6, printed p.8].

14. **Base phase-4 hand-order preservation**
    Active player draws three sequential cards and appends them behind the existing last hand card in draw order [RULES PDF p.6, printed p.8].

15. **Acker-variant phase 4, if approved**
    Each player draws exactly one, starting with active player and continuing clockwise; each appends it to their hand [RULES PDF p.10].

16. **Harvest cleanup and zero yield**
    Harvest the entire selected field; flip exactly the earned number of cards to coin sides and add them to the coin pile; place all remaining harvested cards face-up on discard; the field becomes empty. A below-threshold harvest earns zero but still clears the field [RULES PDF pp.6–7, printed pp.8–9].

17. **Singleton protection**
    With fields of sizes 1 and 2, harvesting the singleton is illegal while harvesting the size-2 field is legal. With occupied field sizes 1 and 1, the quoted prohibition does not bar either singleton [RULES PDF p.7, printed p.9].

18. **Nonterminal deck exhaustion with available discard**
    Drawing the last card empties the deck; shuffle the discard pile and place it face down as the new draw pile [RULES PDF p.8, printed p.10]. Do not assert completion of a partially satisfied draw until question 4 is resolved.

19. **Final exhaustion in phase 2**
    On the third emptying during phase 2, even if only one card was revealed, complete trading/phase 2, then mandatory phase-3 planting; do not execute phase 4; then all players harvest and score [RULES PDF p.8, printed p.10].

20. **Final scoring**
    Hand cards score nothing. Each coin-pile card is one coin; greatest total wins [RULES PDF p.8, printed p.10].

21. **Ackerbohne: two cards, no third field yet**
    Harvesting exactly two turns the board to its three-field side, preserves beans from old fields 1 and 2 in corresponding positions, and discards both harvested Ackerbohnen; it awards no cited coins [RULES PDF p.11].

22. **Ackerbohne: three cards**
    Harvesting exactly three yields three coin cards [RULES PDF p.11]. Whether this also categorically cannot unlock field 3 remains dependent on question 14 because that negative statement appears only in COMPONENTS p.2.

23. **Ackerbohne: two cards with third field already present**
    Candidate expected outcome: no new field and no coins, with harvested cards discarded [RULES PDF p.11; COMPONENTS p.2]. Keep provisional until question 13 is approved.

24. **Clockwise tiebreak without start-player tie**
    For tied non-start players, choose the tied seat with greatest clockwise distance from the fixed start-player seat [RULES PDF pp.3, 8, printed pp.5, 10]. Keep ties involving the start player provisional.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Returned only material source questions and candidate deterministic scenarios, with RULES/COMPONENTS page citations, direct quotes for conflicts, source-role boundaries, and residual risks."
    }
  ],
  "changedFiles": [],
  "testsAddedOrUpdated": [],
  "commandsRun": [],
  "validationOutput": [
    "Reviewed supplied extracted source text and fresh rendered pages, including RULES pages 10-11 and COMPONENTS page 2.",
    "Cross-source and COMPONENTS-internal conflicts were left undecided rather than assigned precedence."
  ],
  "residualRisks": [
    "No source hashes or edition identifiers were available in the reviewed material, so citations use source ID and PDF/rendered page.",
    "Several exact Bohnometer values appear inconsistent inside COMPONENTS; publisher card-face renders should be transcribed before creating hard scoring scenarios.",
    "Deck exhaustion outside phase 2, private-hand visibility, interruption timing, Ackerbohne edge outcomes, and ties involving the start player remain source gaps requiring approval."
  ],
  "noStagedFiles": true,
  "diffSummary": "No files changed; read-only independent source review returned inline.",
  "reviewFindings": [
    "material question: COMPONENTS internally describes two Ackerbohnen both as two coins and as unlocking field 3.",
    "material question: COMPONENTS detail prose conflicts with RULES and its own table on Saubohne thresholds.",
    "material gap: RULES does not fully resolve partial draws or terminal exhaustion outside phase 2."
  ],
  "manualNotes": "COMPONENTS was treated only as user-observation inventory evidence and was never allowed to silently override publisher gameplay rules."
}
```

[38;2;136;136;136m✻ Turn took 2m 16s (Total time 4m 48s · 2 turns)[0m
