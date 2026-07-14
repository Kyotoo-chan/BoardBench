## Edition and scope

The supplied rulebook identifies itself as the German **Exploding Kittens – NSFW Edition**, for **2–5 players**, **56 cards**, copyright **2018**: page 1, “**EXPLODING KITTENS SPIELREGELN (NSFW EDITION)**”, “**SPIELER: 2–5 SPIELMATERIAL: 56 KARTEN**”, and “**COPYRIGHT EXPLODING KITTENS 2018**”. No finer revision or printing identifier is visible, so scenarios should identify it by those fields plus the experiment’s file hash.

Page references below mean PDF/image page 1 or 2.

## Clear implementation requirements

1. **Player-count boundary and initial hands — clear.** Only 2–5 players are supported. Each begins with seven ordinary dealt cards plus one Defuse, for eight cards total. Page 1: “**Teilt danach an jeden Spieler verdeckt 7 Karten aus**” and “**Zusätzlich erhält jeder Spieler eine Karte ‚Entschärfung‘. So starten alle mit 8 Karten auf der Hand.**”

2. **Exploding Kitten count — clear.** Insert exactly `players − 1` kittens: 1/2/3/4 for 2/3/4/5 players. Page 1: “**Nehmt jetzt von den zur Seite gelegten Exploding Kittens eine Karte weniger als Spieler teilnehmen und mischt sie in den Spielstapel. Legt die übrigen Exploding Kittens in die Schachtel zurück.**”

3. **Two-player Defuse exception — clear.** After giving both players their starting Defuse, shuffle only two additional Defuses into the deck; box the other two. Page 1: “**VARIANTE FÜR ZWEI SPIELER: Mischt nur 2 Karten ‚Entschärfung‘ in den Spielstapel und legt die übrigen in die Schachtel zurück.**”

4. **Three-to-five-player Defuses — clear.** All Defuses remaining after the one-per-player distribution are shuffled into the deck. Page 1: “**Mischt zuletzt alle übrigen Karten ‚Entschärfung‘ in den Spielstapel.**”

5. **Derived initial deck sizes — clear.** Applying the quoted 56-card total and setup steps yields 35/30/23/16 cards for 2/3/4/5 players respectively. Supporting text: page 1, “**SPIELMATERIAL: 56 KARTEN**”, “**Teilt danach an jeden Spieler verdeckt 7 Karten aus**”, and the insertion rules above. This derivation is safe for a setup scenario if card identities and counts match the printed list on page 2.

6. **Normal turn and forced draw — clear.** A player may play zero or more cards, but a normal turn ends by drawing exactly one card. Page 1: “**Passen: Spiele keine Karte aus**”; “**Nachdem du die Anweisung der Karte befolgt hast, kannst du weitere Karten spielen, so viele du möchtest**”; and “**Du beendest deinen Zug, indem du die oberste Karte vom Spielstapel ziehst.**”

7. **Empty hand does not eliminate or block a turn — clear.** Page 1: “**Es gibt keine minimale oder maximale Handkartenanzahl. Falls du keine Karten mehr auf der Hand hast – keine Panik. Spiele einfach weiter. Am Ende deines nächsten Zuges ziehst du wieder eine!**”

8. **Attack creates two successive turn obligations — clear.** Attack ends the attacker’s turn without drawing, and the next player must take two turns. Page 2: “**Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.**”

9. **Attack played during an attacked turn hands off two turns — clear.** The printed rule does not add the uncompleted obligation to make three or four turns; it expressly says the next player must perform two. Page 2: “**Spielt dein Opfer dabei selbst eine Karte ‚Angriff‘ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.**”

10. **Skip satisfies only one attacked turn — clear.** Two Skips are needed to discharge both obligations. Page 2: “**Falls du ‚Hops!‘ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal ‚Hops!‘ ausspielen, um beide Züge zu beenden.**”

11. **A Skip immediately ends the current individual turn without a draw — clear.** Page 2: “**Beende sofort deinen Zug, ohne eine Karte zu ziehen.**” Therefore, after the first Skip under Attack, the same player begins the second owed turn.

12. **Nope scope and out-of-turn use — clear.** Nope cancels another card or combination, except Exploding Kitten and Defuse, and can be played while another player is active. Page 2: “**Mit NÖ! setzt du eine andere Karte und deren Aktion außer Kraft, ausgenommen Exploding Kittens und Entschärfung**” and “**Du kannst ein NÖ! auch spielen, wenn du nicht an der Reihe bist.**”

13. **Nope chains — clear for alternating cancellation.** A Nope can cancel another Nope, restoring the underlying action. Page 2: “**Du kannst ein NÖ! auf ein anderes NÖ! legen, um es aufzuheben und daraus ein DOCH! zu machen.**”

14. **Noped cards stay discarded — clear.** Page 2: “**Alle Karten, die ge-NÖ!-t wurden, sind raus und bleiben auf dem Ablagestapel.**”

15. **Nope on Attack leaves the attacker’s turn active — clear.** Page 2 example: “**Doch dann spielt ein anderer Spieler eine NÖ!-Karte aus und setzt deinen Angriff außer Kraft. Du bist weiter am Zug.**” The attacker must continue playing or eventually draw.

16. **Successful Defuse disposition — clear.** Play and discard the Defuse, then reinsert the kitten rather than discarding it. Page 2: “**Spiele sie einfach aus und lege sie auf den Ablagestapel. Lege danach das Exploding Kitten zurück in den Spielstapel.**”

17. **Defuse reinsertion freedom and secrecy — clear.** The player may choose any position, including the top, without looking at or rearranging other cards. Page 2: “**Lege das Exploding Kitten ganz oben auf den Spielstapel**”; “**war geheim an eine Stelle deiner Wahl**”; and “**ohne die anderen Karten anzusehen oder umzusortieren.**”

18. **Elimination contents — clear.** A player without a usable Defuse is eliminated; all remaining hand cards and the kitten go to the discard pile. Page 2: “**Solltest du keine ‚Entschärfung‘ mehr besitzen, war’s das. Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.**”

19. **Terminal condition — clear.** The game ends immediately when only one player remains, who wins. Page 1: “**Eine Runde endet, wenn nur noch ein Spieler am Leben ist: der Gewinner.**” Page 1 also states: “**Der Spieler, der nicht explodiert und als Letzter übrig ist, gewinnt.**”

20. **Pair — clear when the target has at least one card.** Two same-title cards steal one random card from an opponent; this is not limited to Cat cards. Page 2: “**ALLE gleichen Karten [können] als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen**” and “**für alle Karten mit dem gleichen Titel**”.

21. **Triple — clear when the target has cards and the requested title is resolved.** Page 2: “**Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst. Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine solche Karte, hast du Pech gehabt.**”

22. **Five-card combination — clear for five distinct titles and an already-existing discard card.** Page 2: “**Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.**”

23. **Printed instructions of combination components do not execute — clear.** Page 2: “**Wenn du eine Kombination spielst, gelten die Anweisungen auf den Karten nicht.**”

24. **Hand and Look into the Future information are private — clear.** Page 1: “**Haltet dein Blatt stets verdeckt.**” Page 2: “**Schau dir die obersten drei Karten des Spielstapels an und lege sie zurück, ohne deren Reihenfolge zu verändern. Zeige diese Karten bloß nicht deinen Mitspielern.**”

25. **Deck size is public information — clear.** Page 1: “**Du darfst die Anzahl der übrigen Karten im Spielstapel jederzeit nachzählen.**”

## Material ambiguities and specification gaps

Each item below should block a hard scenario that selects one behavior unless the scenario avoids the disputed boundary.

1. **Nope reaction window and priority — ambiguous.** Page 2 says only: “**Du kannst ein NÖ! auch spielen, wenn du nicht an der Reihe bist.**”

   - Behaviour A: every other living player receives an explicit reaction opportunity in turn order; resolution waits until all pass.
   - Behaviour B: Nope is a real-time interrupt, and the first submitted response wins.

   The rulebook gives no priority order, timeout, pass protocol, or point at which an action becomes irrevocably resolved. Block hard timing/order scenarios.

2. **When choices and random effects occur relative to Nope — ambiguous.** Page 2: “**Mit NÖ! setzt du eine andere Karte und deren Aktion außer Kraft**.”

   - Behaviour A: open a Nope window before choosing a target, requested title, donated card, random card, or reinsertion position.
   - Behaviour B: announce some or all parameters first, then permit Nope before applying the effect.

   This affects information leakage and strategic choices. Block scenarios requiring one timing model.

3. **Which cards count as “ge-NÖ!-t” in a canceled combination — ambiguous.** Page 2 says both “**das Pärchen oder die Kombination [kann] durch ein NÖ! in Luft auflösen**” and “**Alle Karten, die ge-NÖ!-t wurden, sind raus und bleiben auf dem Ablagestapel.**”

   - Behaviour A: every component card of the pair/triple/five-card combination remains discarded.
   - Behaviour B: only the conceptual combination/action is canceled, with unclear treatment of its component cards.

   The physical wording strongly suggests A, but it is not explicit enough for a critical hard scenario.

4. **Defuse optionality — ambiguous.** Page 2: “**Wenn du ein Exploding Kitten ziehst, kannst du eine ‚Entschärfung‘ ausspielen, statt zu sterben.**”

   - Behaviour A: having a Defuse creates a player choice; the player may decline and be eliminated.
   - Behaviour B: the environment automatically consumes a Defuse because it is described on page 1 as “**deine einzige Rettung**”.

   Block scenarios asserting automatic consumption or voluntary death.

5. **Turn continuation after Defuse — ambiguous.** Page 2 says “**Dann ist dein Spielzug beendet**” after reinsertion, while Attack can require two “**Spielzüge direkt nacheinander**”.

   - Behaviour A: Defuse ends only the current individual turn; a second Attack-obligated turn begins immediately.
   - Behaviour B: Defuse ends the player’s entire multi-turn obligation.

   “Spielzug” favors A, but the interaction is not explicitly addressed. Block this exact combination.

6. **Outstanding Attack obligation after elimination — ambiguous.** Elimination says the player “**scheidet aus dem Spiel aus**” (page 1), while play otherwise “**geht im Uhrzeigersinn weiter**” (page 1).

   - Behaviour A: elimination ends only the current individual turn; any remaining owed turn disappears and play advances to the next living player.
   - Behaviour B: the remaining obligation transfers to the next living player.

   No transfer rule is given. Block this boundary.

7. **Empty-hand target for Favor, Pair, or Triple — ambiguous.** Favor says “**Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben**”; Pair says “**eine zufällige Karte zu stehlen**” (page 2). Page 1 nevertheless allows a player to have no cards.

   - Behaviour A: selecting an empty-handed target is legal and produces no transfer.
   - Behaviour B: an empty-handed player is not a legal target.

   Block target-legality scenarios involving an empty hand.

8. **Pair randomness distribution — not-testable as a single deterministic expectation.** Page 2 says only “**eine zufällige Karte**”.

   - Behaviour A: uniformly sample physical cards, so duplicate card identities each occupy a separate outcome slot.
   - Behaviour B: use another random procedure, potentially sampling titles first.

   No distribution or RNG method is specified. Exact outcome and uniformity should not be hard-scored from one run.

9. **Shuffle distribution — not-testable.** Page 2: “**Misch den Spielstapel sorgfältig neu.**”

   - Behaviour A: uniformly random permutation.
   - Behaviour B: any sufficiently mixed, nondeterministic permutation.

   The rulebook supplies no measurable distribution. Test only structural invariants unless the evaluator defines an external RNG contract.

10. **Five-card retrieval of a component just played — ambiguous.** Page 2 says “**spielst [du] 5 verschiedene Karten … [und] darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen**”.

   - Behaviour A: the five components enter the discard before retrieval and may themselves be selected.
   - Behaviour B: resolve retrieval against the discard as it existed before playing the combination.

   Block scenarios retrieving one of the five components; retrieving an older discard is safe.

11. **Five-card retrieval of an Exploding Kitten — ambiguous.** The rule says “**eine beliebige Karte aus dem Ablagestapel**” (page 2), while an eliminated player’s kitten “**wande[rt] auf den Ablagestapel**”.

   - Behaviour A: “beliebige” includes a discarded Exploding Kitten, placing it harmlessly in hand.
   - Behaviour B: Exploding Kittens are exceptional hazards and cannot be recovered as ordinary hand cards.

   The literal text supports A but never defines an in-hand kitten. Block this scenario.

12. **Exhausted deck fallback — not-testable/specification gap.** Page 1 asserts: “**der Spielstapel wird nie leer, weil alle Spieler (außer einem) vorher Exploding Kittens ziehen werden**.”

   - Behaviour A: implementations may treat an empty deck as unreachable and raise an invariant error.
   - Behaviour B: combinations and unusual retrieval choices might require graceful handling if the assertion is violated.

   No empty-deck transition is specified. Do not hard-score a particular fallback.

13. **Start-player selection — not-testable.** Page 1: “**Bestimmt einen Startspieler. (Mögliche Kriterien: der beeindruckendste Bart, dominanter Geruch oder die Länge des Blinddarms etc.)**”

   - Behaviour A: callers explicitly supply the starting player.
   - Behaviour B: the implementation chooses randomly or by a fixed policy.

   The listed criteria are suggestions, not an executable rule.

14. **Action naming and serialization — not-testable.** The rulebook specifies physical acts such as “**lege sie OFFEN auf den Ablagestapel**” (page 1), not API identifiers, argument formats, phase enums, or error behavior. Any particular action-string schema requires an evaluator-defined interface contract.

## High-value public-API scenario candidates

1. **Parameterized setup for 2–5 players.** Assert eight-card hands, `n−1` kittens, and the two-player two-extra-Defuse exception. Citations: page 1, “**So starten alle mit 8 Karten auf der Hand**”, “**eine Karte weniger als Spieler teilnehmen**”, and “**Mischt nur 2 Karten ‚Entschärfung‘**”.

2. **Pass/draw and empty hand.** Start an active player with no cards and a safe known top card; passing must remain legal and drawing ends the turn. Citations: page 1, “**Falls du keine Karten mehr … Spiele einfach weiter**” and “**Du beendest deinen Zug, indem du die oberste Karte … ziehst**”.

3. **Attack followed by two Skips.** The victim plays one Skip, remains active for the second owed turn, then plays a second Skip; control advances and no cards are drawn. Citation: page 2, “**überspringst du nur einen der zwei Züge … zweimal ‚Hops!‘**”.

4. **Attack-to-Attack handoff.** During the first attacked turn, the victim plays Attack; the next player owes exactly two turns. Citation: page 2, “**ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen**”.

5. **Nope and counter-Nope.** Attack → Nope leaves the attacker active; Attack → Nope → Nope restores the Attack. Citations: page 2, “**Du bist weiter am Zug**” and “**NÖ! auf ein anderes NÖ! … daraus ein DOCH!**”. Run only if the API exposes a reaction phase.

6. **Defuse with controlled reinsertion.** Draw a kitten, choose Defuse, verify Defuse goes to discard and kitten is reinserted at a selected safe boundary such as top or bottom without changing other-card order. Citations: page 2, “**lege sie auf den Ablagestapel**”, “**ganz oben**”, and “**ohne … anzusehen oder umzusortieren**”.

7. **Pair and Triple with nonempty controlled targets.** Pair transfers a controlled random card; Triple transfers the requested title when present and nothing when absent. Citations: page 2, “**eine zufällige Karte zu stehlen**” and “**Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine … Pech gehabt**”. Inject or seed chance for the Pair.

8. **Five distinct titles recover an older discard.** Choose a card that was already in the discard before the combination; verify component instructions do not execute. Citations: page 2, “**5 verschiedene Karten**”, “**beliebige Karte aus dem Ablagestapel**”, and “**gelten die Anweisungen auf den Karten nicht**”.

9. **Elimination and immediate terminal state.** With two players, a player without Defuse draws the kitten; their hand and kitten enter discard and the other player immediately wins. Citations: page 2, “**Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel**”; page 1, “**wenn nur noch ein Spieler am Leben ist: der Gewinner**”.

## Rules not testable through a public API alone

Absent per-player observations, reaction phases, and privileged inspection hooks, a public API cannot fully test:

- **Hidden hands:** page 1, “**Haltet dein Blatt stets verdeckt.**”
- **Private Look into the Future results:** page 2, “**Zeige diese Karten bloß nicht deinen Mitspielern.**”
- **Secret Defuse position and information leakage:** page 2, “**war geheim an eine Stelle deiner Wahl**”.
- **Nope priority, reaction duration, and simultaneous responses:** page 2 only says “**wenn du nicht an der Reihe bist**”.
- **Physical shuffle quality or probability distribution:** page 2, “**Misch den Spielstapel sorgfältig neu.**”
- **Uniformity of random theft:** page 2 specifies only “**eine zufällige Karte**”.
- **Social selection of the starting player:** page 1, “**Mögliche Kriterien: der beeindruckendste Bart, dominanter Geruch …**”
- **Whether information was gained by physically viewing/reordering cards during reinsertion:** page 2, “**ohne die anderen Karten anzusehen oder umzusortieren**”.

These require either player-specific observation endpoints, deterministic chance injection, event/reaction logs, or evaluator-only state access.