# Wizard Version 1.0 — cited rule facts

- **status:** approved (2026-07-25)
- **condition:** publisher PDF only; base game only
- **source ID:** `WIZARD-RULES`
- **role:** `publisher_rulebook`
- **authorship:** AMIGO Spiel + Freizeit GmbH
- **edition marker:** Version 1.0; copyright MMXCVI (1996)
- **path:** `inputs/games/wizard/game_rules.pdf`
- **SHA-256:** `167254a64b0866266746833c0b98836db51c08171b5b96e25f7461d5bf3dee79`
- **pages:** 2
- **render manifest:** `inputs/games/wizard/game_rules_render_manifest.json` (`pdftoppm` 24.04.0, 150 DPI)
- **condition label:** `publisher_pdf_base_game_only`
- **companion:** none; the rulebook does not delegate rules to another document
- **component appendix:** none
- **excluded inputs:** remembered/web rules, house rules, the page-2 variants, prior implementations, evaluator scenarios, and reviews

## Clear facts

### Components and setup

- **WIZ-INV-01 (`clear`, p. 1):** “Inhalt: 60 Charakterkarten, 1 Block der Wahrheit, 1 Pergament der Regeln.” The game has 60 playing cards plus the score pad and rule sheet.
- **WIZ-INV-02 (`clear`, p. 1):** “Es gibt vier verschiedene Farben: Menschen (blau), Elfen (grün), Zwerge (rot), Riesen (gelb).” Ordinary cards use these four named colors.
- **WIZ-INV-03 (`clear`, p. 1):** “Die jeweils stärkste Karte ist die ‚13‘, die schwächste Karte ist die ‚1‘. Die vier Magierkarten sind immer Trumpf. ... Die vier Narrenkarten sind nie Trumpf.” The packet explicitly identifies ranks 1 and 13 and exactly four Wizards and four Jesters. Page 2 calls the same special type “Zaubererkarten.”
- **WIZ-SETUP-01 (`clear`, p. 1):** “Spieler: 3–6 Lehrlinge.” The base game supports three through six players.
- **WIZ-SETUP-02 (`clear`, p. 1):** “Ein Spieler wird zum Vertrauten der Lehrlinge ernannt. ... Danach mischt der Vertraute die Charakterkarten und teilt sie aus.” One player is initially appointed scorekeeper and performs the first shuffle/deal.

### Rounds and dealing

- **WIZ-DEAL-01 (`clear`, p. 1):** “In der ersten Runde wird nur eine Karte an jeden Spieler ausgeteilt. ... In der zweiten Stichrunde werden an jeden zwei Karten ausgeteilt. ... In der dritten Runde werden drei Karten an jeden verteilt, dann vier Karten usw.” Round number equals cards dealt to each player.
- **WIZ-DEAL-02 (`clear`, p. 1):** “Karten, die nicht an die Spieler verteilt werden, kommen als verdeckter Stapel in die Tischmitte.” Undealt cards form the face-down center stack.
- **WIZ-DEAL-03 (`clear`, p. 1):** “Nach jeder Stichrunde wechselt ... die Charakterkarten zu verteilen, im Uhrzeigersinn an den jeweils linken Lehrling.” Dealer responsibility moves one player clockwise after every round.
- **WIZ-END-01 (`clear`, p. 2):** “Im Spiel sind 60 Charakterkarten. Die Lehrlinge spielen so lange, bis in der letzten Stichrunde alle Karten ausgeteilt wurden. Bei 6 Teilnehmern ist das die 10. Stichrunde, bei 5 Teilnehmern die 12. Stichrunde, bei 4 Teilnehmern die 15. und bei 3 Teilnehmern die 20. Stichrunde.” The final round is `60 / players`, namely rounds 10, 12, 15, and 20 for six, five, four, and three players.

### Trump and predictions

- **WIZ-TRUMP-01 (`clear`, p. 1):** “Nachdem die Charakterkarten ausgeteilt wurden, wird vom Stapel die oberste Karte umgedreht ... Diese Karte bestimmt ... die Trumpffarbe.” A revealed ordinary card sets its color as trump.
- **WIZ-TRUMP-02 (`clear`, p. 1):** “Ist die aufgedeckte Karte ein Narr, dann gibt es in dieser Runde keine Trumpffarbe. Ist die aufgedeckte Karte ein Zauberer, dann darf der Lehrling, der die Karten ausgeteilt hat, eine Trumpffarbe bestimmen, aber erst, nachdem er sich seine Karten angeschaut hat.” A revealed Jester means no trump; a revealed Wizard gives the dealer the trump-color decision after seeing their hand.
- **WIZ-TRUMP-03 (`clear`, p. 1):** “In der letzten Stichrunde gibt es keinen Trumpf, weil es keinen Stapel gibt.” The final round has no trump.
- **WIZ-BID-01 (`clear`, p. 1):** “Nachdem sich jeder Lehrling seine Karten angeschaut hat, muss er vorhersagen, wie viele Stiche er in dieser Runde wohl machen wird.” Every player predicts their own trick count after seeing their hand.
- **WIZ-BID-02 (`clear`, p. 1):** “Der Reihe nach geben die Lehrlinge ihre Vorhersagen ... Es beginnt der linke Nachbar des Kartengebers. Die Tipps werden auf dem Block der Wahrheit notiert. Vor dem ersten Stich sollte der Vertraute die Vorhersagen noch einmal für alle wiederholen.” Prediction starts with the player left of the dealer and is public before play in the base game.

### Legal play and trick winner

- **WIZ-PLAY-01 (`clear`, p. 1):** “Der linke Nachbar des Kartengebers spielt die erste Karte für den ersten Stich aus. Die anderen Lehrlinge folgen im Uhrzeigersinn. ... Der Gewinner nimmt den Stich ... und eröffnet den neuen Stich indem er eine Karte ausspielt.” The dealer’s left neighbor leads the first trick; play proceeds clockwise; each later trick is led by the prior trick winner.
- **WIZ-PLAY-02 (`clear`, p. 1):** “Eine angespielte Farbe muss bedient werden. Ist das nicht möglich, kann der Lehrling eine Farbe abwerfen oder Trumpf spielen.” A player holding the led ordinary color must follow it; otherwise any ordinary color or trump may be played.
- **WIZ-PLAY-03 (`clear`, p. 1):** “Zauberer- und Narrenkarten dürfen immer gespielt werden, auch wenn man bedienen könnte.” A Wizard or Jester is always a legal play and does not itself have to follow suit.
- **WIZ-WIN-01 (`clear`, p. 2):** “Es gewinnt den Stich: Die erste Zaubererkarte in einem Stich, oder die höchste Karte in der Trumpffarbe, oder die höchste Karte in der zuerst ausgespielten Farbe, wenn weder Trumpf noch Zauberer im Stich sind.” Winner priority is first Wizard, otherwise highest trump, otherwise highest card of the led color.
- **WIZ-WIN-02 (`clear`, p. 2):** “Wird ein Stich mit einer Zaubererkarte eröffnet ... Der Stich geht in jedem Fall an den ersten Zauberer.” A Wizard lead makes every following card legal, and the first Wizard wins even if later Wizards are played.
- **WIZ-WIN-03 (`clear`, p. 2):** “Wird ein Stich mit einer Narrenkarte eröffnet, dann darf als zweite Karte jede beliebige Karte gespielt werden. Erst die zweite Karte bestimmt die Farbe, die bedient werden muss.” If a Jester leads and the second card is ordinary, that second card establishes the led color.
- **WIZ-WIN-04 (`clear`, p. 2):** “Werden in einem Stich nur Narren gespielt, dann gewinnt die erste Narrenkarte den Stich.” In an all-Jester trick, the first Jester wins.

### Scoring and end

- **WIZ-SCORE-01 (`clear`, p. 2):** “Der Lehrling, der die Anzahl seiner gewonnenen Stiche genau vorhersagen konnte, erhält 20 Erfahrungspunkte plus 10 Punkte pro gewonnenen Stich.” An exact prediction scores `20 + 10 × tricks won`.
- **WIZ-SCORE-02 (`clear`, p. 2):** “Wer daneben getippt hat, verliert jeweils 10 Erfahrungspunkte für jeden Stich, den er über oder unter seiner Vorhersage liegt.” A miss scores `-10 × absolute(prediction − tricks won)`.
- **WIZ-END-02 (`clear`, p. 2):** “Die letzte Stichrunde wird noch abgerechnet. Gewonnen hat der Zauberlehrling mit der höchsten Erfahrungspunktzahl.” The final round is scored before the highest final score wins.

## Approved human decisions (2026-07-25)

These decisions make omitted executable details explicit for the evaluator. They are not silently attributed to the publisher and are not supplied to the original PDF-only implementer.

- **WIZ-DEC-SCOPE (`human_decision`):** Only the base game is implemented and scored. The separately headed page-2 variants are excluded as gameplay rules and actions; scenarios may cite them only as negative or contrast evidence that a restriction is not part of the base game.
- **WIZ-DEC-INV (`human_decision`, p. 1 basis):** The 60-card deck is modeled as exactly one rank 1–13 in each of the four named colors, plus four Wizards and four Jesters: `4 × 13 + 4 + 4 = 60`. “Magierkarten” and “Zaubererkarten” denote the same Wizard type.
- **WIZ-DEC-FLOW (`human_decision`, p. 1 basis):** Player 0 is the first dealer/scorekeeper. At every round boundary all 60 cards are collected and freshly shuffled before the next larger deal. Dealer rotation remains clockwise.
- **WIZ-DEC-TRUMP (`human_decision`, p. 1 basis):** A revealed Wizard requires the dealer to choose and publicly announce exactly one of the four colors; declining to choose trump is not legal.
- **WIZ-DEC-BID (`human_decision`, p. 1 basis):** Predictions proceed clockwise from the dealer’s left neighbor and are integer values from 0 through the current hand size. The base game imposes no restriction on the sum of predictions.
- **WIZ-DEC-JESTER (`human_decision`, p. 2 basis):** After one or more leading Jesters, the first subsequently played ordinary colored card establishes the led color. If a Wizard appears before any ordinary colored card, the trick remains colorless, all remaining players may play any card, and the first Wizard wins.
- **WIZ-DEC-TIE (`human_decision`, p. 2 basis):** Players tied for the highest final score are joint winners.
- **WIZ-DEC-PRIVACY (`human_decision`, pp. 1–2 basis):** Base-game hands are private: each player observes their own hand and only opponents’ hand sizes. The explicitly separate Hellsehen variant is the only supplied mode that reverses first-round card visibility.

## Explicitly excluded rules

- **WIZ-X-VARIANTS (`not_testable`, p. 2):** Plus/minus Eins, Verdeckter Tipp, Geheime Vorhersage, Hellsehen, and Einfarbig are optional variants and are outside the approved base-game scope.
- **WIZ-X-HOUSE-WIZARD (`not_testable`, user statement 2026-07-25):** The household rule that a later/second Wizard can win is excluded. It conflicts with `WIZ-WIN-01` and `WIZ-WIN-02`, which award the trick to the first Wizard.
- **WIZ-X-HOUSE-BIDS (`not_testable`, user statement 2026-07-25):** Requiring the sum of predictions not to equal the available tricks is excluded from the base game. The publisher packet presents that restriction only under the separate “Plus/minus Eins” variant.

## Remaining non-material gaps

- The publisher does not specify a real-world method for selecting the first scorekeeper/dealer, handling player departure, correcting a misrecorded prediction, or resolving accidental physical misdeals. The environment uses the approved deterministic start and treats malformed actions as invalid rather than modeling social corrections.
- Chips, pencils, and private slips mentioned as suggestions or variant aids are presentation devices, not modeled components.
- No material base-game ambiguity remains unresolved for the approved environment and scenario scope.
