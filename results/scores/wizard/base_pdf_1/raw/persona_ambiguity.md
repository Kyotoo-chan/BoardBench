The implementation is largely aligned with the approved human decisions. The main findings are:

- One material source omission remains unresolved: the order in which cards are dealt.
- One source ambiguity was resolved by an approved decision, but the implementation does not fully follow that decision: a Wizard played after leading Jesters should leave the trick colorless.
- The remaining implementation choices are reasonable assumptions explicitly authorized by approved decisions.

## Missing rules

### 1. Exact deck composition

- **Page 1 quote:** “Die jeweils stärkste Karte ist die ‚13‘, die schwächste Karte ist die ‚1‘. Die vier Magierkarten sind immer Trumpf. … Die vier Narrenkarten sind nie Trumpf.”
- **Plausible interpretations:**
  1. Each of the four colors contains exactly one card of every rank 1–13.
  2. The ordinary cards use ranks bounded by 1 and 13, but intermediate ranks or multiplicities need not be uniform.
- **Implementation:** Constructs one rank 1–13 in each color plus four Wizards and four Jesters at [implementation.py:9](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:9) and [implementation.py:19](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:19).
- **Affected behavior:** Card inventory, possible hands, trump reveals, legal plays, and all downstream results.
- **Approved decision:** Yes, `WIZ-DEC-INV` explicitly selects the implementation’s composition at [canonical_rulefacts.md:64](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/canonical_rulefacts.md:64).
- **Clarification:** “Each color contains exactly one card numbered 1 through 13; the deck also contains four Wizards and four Jesters.”

### 2. Selection of the first dealer/scorekeeper

- **Page 1 quote:** “Ein Spieler wird zum Vertrauten der Lehrlinge ernannt. … Danach mischt der Vertraute die Charakterkarten und teilt sie aus.”
- **Plausible interpretations:**
  1. Players choose the initial dealer by agreement or some unmodeled selection procedure.
  2. A fixed seat, such as player 0, is always the initial dealer.
- **Implementation:** Assigns player 0 as dealer and player 1 as the first leader at [implementation.py:81](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:81).
- **Affected behavior:** Initial dealer, first bidder, first leader, trump chooser, hands under a fixed shuffle, and dealer rotation.
- **Approved decision:** Yes, `WIZ-DEC-FLOW` selects player 0 at [canonical_rulefacts.md:65](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/canonical_rulefacts.md:65).
- **Clarification:** “Player 0 is the first dealer and scorekeeper.”

### 3. Collection and shuffling between rounds

- **Page 1 quotes:** “Danach mischt der Vertraute die Charakterkarten und teilt sie aus.” Also: “Nach jeder Stichrunde wechselt … die Charakterkarten zu verteilen, im Uhrzeigersinn an den jeweils linken Lehrling.”
- **Plausible interpretations:**
  1. Collect all 60 cards and shuffle afresh before every round.
  2. Collect the cards but retain or otherwise reuse their order; the text expressly mentions shuffling only during preparation.
- **Implementation:** Reassembles all zones, increments the dealer, reshuffles, and deals again at [implementation.py:181](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:181).
- **Affected behavior:** Chance state, every later hand and trump reveal, and consequently all legal actions and scores.
- **Approved decision:** Yes, `WIZ-DEC-FLOW` requires collection and fresh shuffling every round.
- **Clarification:** “After scoring each round, collect all 60 cards, shuffle them, and have the next dealer deal the following round.”

### 4. Order of dealing — unresolved

- **Page 1 quote:** “In der ersten Runde wird nur eine Karte an jeden Spieler ausgeteilt. … In der zweiten Stichrunde werden an jeden zwei Karten ausgeteilt.”
- **Plausible interpretations:**
  1. Deal one card at a time clockwise, starting with the player left of the dealer.
  2. Deal starting with the dealer, counterclockwise, or distribute each player’s complete hand as a block.
- **Implementation:** Deals one card at a time clockwise, beginning left of the dealer, at [implementation.py:97](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:97).
- **Affected behavior:** Exact hands under a fixed shuffled deck, trump card identity, private information, predictions, and potentially the terminal result.
- **Approved decision:** No. `WIZ-DEC-FLOW` identifies the first dealer, reshuffling, and dealer rotation, but does not specify dealing order. The general assertion that no material gaps remain does not itself choose an order.
- **Clarification:** “Deal one card at a time clockwise, beginning with the player to the dealer’s left, until every player has the round’s required number of cards.”

### 5. Tie handling

- **Page 2 quote:** “Gewonnen hat der Zauberlehrling mit der höchsten Erfahrungspunktzahl.”
- **Plausible interpretations:**
  1. All players tied at the highest score are joint winners.
  2. A tiebreaker, additional round, or single-winner selection is required.
- **Implementation:** Ends immediately after final scoring and returns each player’s raw score; it does not construct a separate winner or tiebreak state ([implementation.py:178](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:178), [implementation.py:194](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:194)). Equal maximum scores are preserved, which is compatible with joint winners, although the winner set is not explicitly represented.
- **Affected behavior:** Terminal result and winner reporting.
- **Approved decision:** Yes, `WIZ-DEC-TIE` makes tied leaders joint winners.
- **Clarification:** “If several players share the highest final score, all of them win.”

## Ambiguous rules

### 6. Whether a revealed Wizard makes trump selection mandatory

- **Page 1 quote:** “Ist die aufgedeckte Karte ein Zauberer, dann darf der Lehrling, der die Karten ausgeteilt hat, eine Trumpffarbe bestimmen.”
- **Plausible interpretations:**
  1. The dealer must select exactly one of the four colors.
  2. “Darf” is permissive: the dealer may decline, leaving the round without trump.
- **Implementation:** Enters a mandatory `choose_trump` phase and offers only the four colors at [implementation.py:103](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:103) and [implementation.py:123](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:123).
- **Affected behavior:** Dealer legal actions, public trump state, following tricks, and winners.
- **Approved decision:** Yes, `WIZ-DEC-TRUMP` makes a choice mandatory.
- **Clarification:** “When a Wizard is revealed, the dealer must publicly choose exactly one of the four colors as trump.”

### 7. Prediction domain and total-prediction restriction

- **Page 1 quote:** “Jeder Lehrling … muss er vorhersagen, wie viele Stiche er in dieser Runde wohl machen wird.”
- **Page 2 contrast:** Under “Plus/minus Eins”: “Die Anzahl der gewollten Stiche aller Lehrlinge darf aber nicht mit der Zahl der möglichen Stiche übereinstimmen.”
- **Plausible interpretations:**
  1. Base-game predictions are integers from zero through the hand size, with no restriction on their sum.
  2. Predictions may use a broader numerical range, or the Plus/minus-Eins total restriction might be mistaken for a general rule.
- **Implementation:** Offers `0..round_number` and places no condition on the total at [implementation.py:124](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:124).
- **Affected behavior:** Legal prediction actions, public state, scoring, and possible strategies.
- **Approved decision:** Yes, `WIZ-DEC-BID` adopts exactly that range and excludes the sum restriction from the base game.
- **Clarification:** “Each prediction must be a whole number from zero through the number of cards held; in the base game, the predictions may total any value.”

### 8. Multiple leading Jesters and an intervening Wizard

- **Page 2 quotes:** “Wird ein Stich mit einer Narrenkarte eröffnet, dann darf als zweite Karte jede beliebige Karte gespielt werden. Erst die zweite Karte bestimmt die Farbe, die bedient werden muss.” Also: “Werden in einem Stich nur Narren gespielt, dann gewinnt die erste Narrenkarte den Stich.”
- **Plausible interpretations:**
  1. Ignore consecutive leading Jesters until the first ordinary card establishes the led color; if a Wizard appears first, the trick remains colorless.
  2. Only the literal second card can establish a color; alternatively, an ordinary card played after a Jester–Wizard sequence may still establish a suit for later players.
- **Implementation:** Every special leaves `led_suit` unset, and the first ordinary card at any later position sets it ([implementation.py:150](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:150)). Once set, later players holding that suit must follow it ([implementation.py:127](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:127)). The first Wizard nevertheless wins ([implementation.py:159](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:159)).
- **Affected behavior:** Legal actions after sequences such as Jester–Wizard–ordinary; the trick winner remains the first Wizard, but later players can be improperly forced to follow the subsequently established color.
- **Approved decision:** Yes. `WIZ-DEC-JESTER` says that if a Wizard appears before an ordinary card, the trick remains colorless and all remaining players may play anything. The implementation therefore does **not** follow the approved resolution for this branch. It does follow the approved rule for several Jesters followed by an ordinary card.
- **Clarification:** “After leading Jesters, the first ordinary card sets the led color only if no Wizard has yet been played; once a Wizard appears, the trick remains colorless and every remaining card is legal.”

### 9. Hand privacy

- **Page 1 quote:** “Nachdem sich jeder Lehrling seine Karten angeschaut hat …”
- **Page 2 contrast, Hellsehen variant:** “In der ersten Runde hält jeder Lehrling seine Karte ungesehen vor seine Stirn, so dass alle Lehrlinge außer ihm selbst die Karte sehen können.”
- **Plausible interpretations:**
  1. Base-game hands are private, and players see only their own cards.
  2. The rulebook merely describes looking at cards and never expressly prohibits showing or exposing them.
- **Implementation:** Player observations contain the requesting player’s cards and only opponents’ hand sizes at [implementation.py:253](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:253).
- **Affected behavior:** Information available for predictions and card play.
- **Approved decision:** Yes, `WIZ-DEC-PRIVACY` explicitly requires private hands.
- **Clarification:** “Each player may see their own hand, but not the identities of cards in any opponent’s hand.”

## Contradictory rules

No material contradiction appears within the base-game rules. In particular:

- “Wizards are always trump” and “the first Wizard wins” describe priority consistently.
- The prediction-total restriction appears only under the separately headed Plus/minus-Eins variant.
- The later-Wizard-wins household rule is expressly excluded and contradicts the canonical first-Wizard rule, not another canonical base-game passage.

## Merely untestable or non-material matters

These omissions do not define additional gameplay branches in the approved model:

- The physical or social method used to appoint the first scorekeeper.
- The exact real-world randomness mechanism used for shuffling. The seeded algorithm at [implementation.py:70](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vMtBTR/boardbench_wizard_codex_ag_ambiguity_wihj30o2/implementation.py:70) is reproducibility infrastructure, not a publisher rule.
- Misdeals, player departure, correction of misrecorded predictions, and handling pencils, chips, or score slips.
- All rules beneath the page-2 “Varianten” heading. `WIZ-DEC-SCOPE` and `WIZ-X-VARIANTS` explicitly place them outside the base-game action space.

## Material-assumption summary

The implementation assumes an exact 60-card composition, player 0 as first dealer, complete collection and fresh shuffling each round, mandatory four-color trump selection after a revealed Wizard, predictions from zero through hand size with unrestricted totals, private hands, and no terminal tiebreak. Those assumptions are all covered by approved human decisions.

Two matters require attention:

1. **Unresolved specification:** Neither the publisher text nor an approved decision specifies dealing order; the code assumes round-robin clockwise from the dealer’s left.
2. **Resolved but implemented differently:** After Jester(s) followed by a Wizard, the approved decision keeps the trick colorless, while the code allows a later ordinary card to establish a suit and restrict subsequent legal plays.