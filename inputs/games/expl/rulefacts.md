---
status: approved
game: expl
edition: "Exploding Kittens NSFW Edition, German, 2018, 2 pages, 2-5 players, 56 cards"
rulebook: inputs/games/expl/game_rules.pdf
sha256: f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853
approved_by_user: 2026-07-14
corrected_by_user: 2026-07-15
---

# Approved canonical rule facts

Only the archived PDF above is a rule source. API conventions and human decisions below are explicit adjudications, not claims that the printed rulebook says more than it does.

## Setup

| ID | Page | Direct quote | Approved expectation |
|---|---:|---|---|
| SET-01 | 1 | “Legt alle 4 Exploding Kittens und alle 6 Karten „Entschärfung“ beiseite.” | Remove all four Kittens and all six Defuses before dealing. |
| SET-02 | 1 | “Mischt die restlichen Karten sorgfältig. Teilt danach an jeden Spieler verdeckt 7 Karten aus.” | Deal seven hidden cards to each player. |
| SET-03 | 1 | “Zusätzlich erhält jeder Spieler eine Karte „Entschärfung“. So starten alle mit 8 Karten auf der Hand.” | Each player starts with eight cards including one Defuse. |
| SET-04 | 1 | “Nehmt jetzt von den zur Seite gelegten Exploding Kittens eine Karte weniger als Spieler teilnehmen und mischt sie in den Spielstapel.” | Insert exactly `player_count - 1` Kittens. |
| SET-05 | 1 | “Legt die übrigen Exploding Kittens in die Schachtel zurück.” | Unused Kittens are out of play. |
| SET-06 | 1 | “Mischt zuletzt alle übrigen Karten „Entschärfung“ in den Spielstapel.” | With 3-5 players, all Defuses remaining after starting hands enter the deck. |
| SET-07 | 1 | “Mischt nur 2 Karten „Entschärfung“ in den Spielstapel und legt die übrigen in die Schachtel zurück.” | With two players, exactly two additional Defuses enter the deck. |
| SET-08 | 1 | “Halte dein Blatt stets verdeckt.” | Hands are private to their owners. |
| SET-09 | 1 | “Mischt den Spielstapel und legt ihn verdeckt in die Mitte des Tisches.” | The draw pile is shuffled and hidden. |

## Turn flow

| ID | Page | Direct quote | Approved expectation |
|---|---:|---|---|
| TURN-01 | 1 | “Passen: Spiele keine Karte aus.” | Playing no card before the mandatory draw is legal. |
| TURN-02 | 1 | “Wähle eine deiner Handkarten aus, lege sie OFFEN auf den Ablagestapel und befolge ihre Anweisung.” | A played card is public, discarded, and resolved. |
| TURN-03 | 1 | “Nachdem du die Anweisung der Karte befolgt hast, kannst du weitere Karten spielen, so viele du möchtest.” | The current player may play zero or more cards before the turn-ending action. |
| TURN-04 | 1 | “Du beendest deinen Zug, indem du die oberste Karte vom Spielstapel ziehst.” | A normal turn ends by drawing the top card. |
| TURN-05 | 1 | “Die Partie geht im Uhrzeigersinn weiter.” | Turn order advances through living players clockwise. |
| TURN-06 | 1 | “Es gibt keine minimale oder maximale Handkartenzahl.” | There is no hand-size bound. |
| TURN-07 | 1 | “Falls du keine Karten mehr auf der Hand hast – keine Panik. Spiele einfach weiter. Am Ende deines nächsten Zuges ziehst du wieder eine!” | An empty hand neither eliminates a player nor prevents the draw action. |
| TURN-08 | 1 | “Du darfst die Anzahl der übrigen Karten im Spielstapel jederzeit nachzählen.” | Draw-pile size is public; identities/order remain hidden. |

## Explosion, Defuse, elimination, and terminal result

| ID | Page | Direct quote | Approved expectation |
|---|---:|---|---|
| EXP-01 | 2 | “Diese Karte musst du sofort offen zeigen.” | A Kitten drawn from the draw pile is revealed immediately. |
| EXP-02 | 2 | “Solltest du keine „Entschärfung“ mehr besitzen, war’s das.” | A player without a Defuse is eliminated. |
| EXP-03 | 2 | “Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.” | On elimination, the player's hand and the Kitten enter the discard pile. |
| DEF-01 | 2 | “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.” | **Human decision:** if the player has a Defuse, it must be used; voluntary elimination is not offered. |
| DEF-02 | 2 | “Spiele sie einfach aus und lege sie auf den Ablagestapel.” | The used Defuse enters the discard pile. |
| DEF-03 | 2 | “Lege danach das Exploding Kitten zurück in den Spielstapel, und zwar geheim an eine Stelle deiner Wahl, ohne die anderen Karten anzusehen oder umzusortieren.” | The player chooses any reinsertion position; the position is secret and other cards keep their relative order. |
| DEF-04 | 2 | “Dann ist dein Spielzug beendet.” | Defuse ends the current individual turn. **Human decision:** any further turn owed by Attack must still be taken. |
| TERM-01 | 1 | “Eine Runde endet, wenn nur noch ein Spieler am Leben ist: der Gewinner.” | The game becomes terminal immediately when one player remains. |
| TERM-02 | 1 | “Der Spieler, der nicht explodiert und als Letzter übrig ist, gewinnt.” | The sole survivor wins. API returns are `+1` for the winner and `-1` for every eliminated player. |

## Named cards

| ID | Page | Direct quote | Approved expectation |
|---|---:|---|---|
| SKIP-01 | 2 | “Beende sofort deinen Zug, ohne eine Karte zu ziehen.” | Hops!/Skip ends the current individual turn without drawing. |
| SKIP-02 | 2 | “Falls du „Hops!“ ausspielst, um einen Angriff abzuwehren, überspringst du nur einen der zwei Züge. Du müsstest schon zweimal „Hops!“ ausspielen, um beide Züge zu beenden.” | Under Attack, one Skip consumes exactly one owed turn. |
| ATK-01 | 2 | “Du beendest deinen eigenen Zug, ohne eine Karte zu ziehen, und zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.” | Attack ends the attacker's turn without drawing and gives the next living player two turns. |
| ATK-02 | 2 | “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.” | **Human decision:** an Attack played during an Attack replaces the remaining obligation; the following player owes exactly two turns. |
| ATK-03 | 1-2 | “scheidet aus dem Spiel aus” / “Die Partie geht im Uhrzeigersinn weiter.” | **Human decision:** if an attacked player is eliminated, that player's remaining owed turns disappear. |
| FUT-01 | 2 | “Schau dir die obersten drei Karten des Spielstapels an und lege sie zurück, ohne deren Reihenfolge zu verändern.” | The current player privately sees the top three without reordering. **Human decision:** if fewer than three remain, show all remaining cards. |
| FUT-02 | 2 | “Zeige diese Karten bloß nicht deinen Mitspielern.” | Other players do not receive the preview. |
| SHUF-01 | 2 | “Misch den Spielstapel sorgfältig neu.” | Shuffle changes only draw-pile order. No exact probability distribution is hard-scored. |
| FAV-01 | 2 | “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben. Dieser Spieler entscheidet, welche Karte du bekommst.” | Target selects and transfers a card. **Human decision:** empty-handed players are not legal targets. |
| NOPE-01 | 2 | “Mit NÖ! setzt du eine andere Karte und deren Aktion außer Kraft, ausgenommen Exploding Kittens und Entschärfung.” | Nope cancels a pending card/combination except Kitten and Defuse. |
| NOPE-02 | 2 | “Du kannst ein NÖ! auf ein anderes NÖ! legen, um es aufzuheben und daraus ein DOCH! zu machen.” | Each further Nope toggles whether the underlying action resolves. |
| NOPE-03 | 2 | “Du kannst ein NÖ! auch spielen, wenn du nicht an der Reihe bist.” | Every living player holding Nope may react out of turn. |
| NOPE-04 | 2 | “Alle Karten, die ge-NÖ!-t wurden, sind raus und bleiben auf dem Ablagestapel.” | Played and cancelled cards remain discarded. |
| NOPE-05 | 2 | “setzt deinen Angriff außer Kraft. Du bist weiter am Zug.” | A cancelled action has no effect and the original player continues the turn. |

## Combinations and discard retrieval

| ID | Page | Direct quote | Approved expectation |
|---|---:|---|---|
| PAIR-01 | 2 | “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden, um einem Mitspieler eine zufällige Karte zu stehlen.” | Any two same-title cards can steal one random card. Empty-handed players are not legal targets. |
| TRI-01 | 2 | “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.” | Three same-title cards request a named card. |
| TRI-02 | 2 | “Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine solche Karte, hast du Pech gehabt.” | Transfer occurs only if the target holds the requested title. |
| FIVE-01 | 2 | “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” | Five distinct titles are played to the discard, then the player retrieves any chosen card now in that discard, including an Exploding Kitten or one of the five just-played component cards. |
| FIVE-02 | 1-2 | “Wenn du ein Exploding Kitten ziehst …” / “eine beliebige Karte aus dem Ablagestapel nehmen” | **Human decision:** taking a Kitten from the discard is not drawing it from the draw pile, so it does not explode and remains in hand. It cannot be played singly but may participate in same-title combinations. |
| COMBO-01 | 2 | “Wenn du eine Kombination spielst, gelten die Anweisungen auf den Karten nicht.” | Printed instructions of cards used in a pair/triple/five-card combination do not execute. |

## Approved interface conventions

These conventions make the fixed BoardBench API executable and are not sourced game rules:

- `Game()` defaults to two players; implementations may accept an optional `num_players` and seed.
- Player `0` is the deterministic default start player.
- Nonterminal returns are zero for every player; terminal returns are `+1/-1` as above.
- Random outcomes may use a seeded standard-library RNG.
- Rulebook choices, including targets, requested titles, donated cards, reinsertion positions, and discard retrieval, must be explicit legal actions/phases rather than silently selected by the engine.
- For the physical real-time NÖ! rule, the turn-based environment uses a deterministic clockwise reaction opportunity. Each eligible living player may pass or play NÖ!; the chain closes after all eligible players consecutively pass. Targets/parameters are announced before that window. Reaction priority itself is not a hard rule-fidelity scenario.

## Adjudication correction

On 2026-07-15, after rereading the action order, the user corrected the earlier pre-existing-discard restriction: the five cards are played and discarded before retrieval, so one of those five components may be selected immediately. Historical generation and judge artifacts remain unchanged; judge findings that penalize this self-retrieval are evaluator false positives under the corrected rubric.

## Still ambiguous or not hard-testable

The following remain visible rather than being scored as failures:

- the physical timing/priority speed of NÖ! reactions;
- probability distributions for shuffling and random theft;
- social start-player selection;
- which physical copy is selected when multiple identical cards are in the discard; title-equivalent copies have the same public behaviour;
- secret information cannot be fully verified without player-specific observations;
- setup/card-count internals and rare hands cannot be forced through the current minimal public API;
- exact numeric action encoding and display language are evaluator interface choices.
