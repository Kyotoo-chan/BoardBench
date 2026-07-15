## Findings

1. **Elimination fails to discard the eliminated player’s hand**

- Fact ID: `EXP-03`
- Evidence type: `rule_quote`
- Page 2: “Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.”
- Code: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:154), especially lines 160–162.
- Expected: On explosion without a Defuse, discard the Kitten and every remaining card in that player’s hand.
- Actual: Only the Kitten is appended to `discard`; the eliminated player’s hand remains intact.
- Severity: **Major**
- Confidence: **High**

2. **Defusing the first of two attacked turns incorrectly ends the entire obligation**

- Fact ID: `DEF-04`
- Evidence type: `human_decision`
- Page 2: “Dann ist dein Spielzug beendet.” The approved decision adds: any further turn owed by Attack must still be taken.
- Code: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:136), lines 136–137.
- Expected: Defuse ends only the current individual turn. If the player owed two turns and exploded on the first, they still owe the second.
- Actual: Every reinsertion sets `player` to the next player and resets `turns_left` to `1`, discarding any remaining attacked turn.
- Severity: **Major**
- Confidence: **High**

3. **Five-card combinations cannot retrieve a newly discarded component**

- Fact ID: `FIVE-01`
- Evidence type: `human_decision`
- Page 2: “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Code: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:89), lines 89–94 and 175–177.
- Expected: The five components enter the discard before retrieval, so any of them may immediately be selected. This is explicitly confirmed by the adjudication correction.
- Actual: Legal retrieval choices are generated solely from the discard as it existed before playing the five cards. If the discard is empty, no five-card action is offered at all.
- Severity: **Major**
- Confidence: **High**

4. **Exploding Kittens and Defuses are wrongly excluded from combinations**

- Fact IDs: `PAIR-01`, `TRI-01`, `FIVE-01`, `FIVE-02`
- Evidence type: `human_decision` for `FIVE-02`; `rule_quote` for the other facts.
- Page 2:
  - “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden …”
  - “Wie ein Pärchen …”
  - “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst …”
  - Approved `FIVE-02` decision: a retrieved Kitten may participate in same-title combinations.
- Code: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:83), lines 83–90.
- Expected: Any qualifying same-title cards can form a pair/triple, including Kittens held through discard retrieval; five distinct titles are not restricted by card type.
- Actual: `EK` and `DEFUSE` are explicitly excluded from pairs, triples, and five-card component sets.
- Severity: **Major**
- Confidence: **High**

5. **Triple requests expose the target’s hand and cannot request an absent title**

- Fact IDs: `SET-08`, `TRI-01`, `TRI-02`
- Evidence type: `rule_quote`
- Pages 1–2:
  - “Halte dein Blatt stets verdeckt.”
  - “Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine solche Karte, hast du Pech gehabt.”
- Code: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:71), lines 71–72 and 140–143.
- Expected: The acting player names a title without learning whether the target holds it; an absent-title request is legal and simply transfers nothing.
- Actual: Legal request titles are generated directly from `s.hands[s.target]`, disclosing the target’s distinct titles and preventing a genuine request for an absent title. The generic “not present” action is not a named request.
- Severity: **Major**
- Confidence: **High**

6. **A triple’s requested title is announced after the Nope window**

- Fact ID: `NOPE-06`
- Evidence type: `human_decision`
- Page 2: “Mit NÖ! setzt du eine andere Karte und deren Aktion außer Kraft.”
- Approved decision: the complete proposed action—including target and requested title—must be announced before the NÖ!/DOCH! reaction window.
- Code: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:171), lines 171–174, then 127 and 140–143.
- Expected: Playing a triple specifies both the target and requested title before reactions begin.
- Actual: The pending triple contains only its component title and target. The requested title is chosen later, after the reaction chain resolves.
- Severity: **Major**
- Confidence: **High**

7. **A restored theft can crash or deadlock after the target spends its last card as Nope**

- Fact ID: `NOPE-07`
- Evidence type: `human_decision`
- Page 2: “Alle Karten, die ge-NÖ!-t wurden, sind raus und bleiben auf dem Ablagestapel.”
- Approved decision: if a legal target spends its last card during the reaction chain and the action is restored, it resolves without a transfer.
- Code:
  - Pair resolution: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:124), lines 124–126.
  - Favor donation phase: lines 69–70 and 138–139.
- Expected: The restored action completes harmlessly without transferring a card.
- Actual:
  - Pair calls `random.choice()` on the now-empty hand, raising an exception.
  - Favor enters a donation phase with no legal actions, leaving the game stuck.
- Severity: **Critical**
- Confidence: **High**

8. **Shuffle leaves an earlier preview marked as current knowledge**

- Fact ID: `FUT-03`
- Evidence type: `human_decision`
- Page 2: “Misch den Spielstapel sorgfältig neu.”
- Approved decision: after Shuffle changes deck order, an earlier preview is stale and must not be presented as current top-card knowledge.
- Code: [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_rule_fidelity_22t7k4wv/implementation.py:120), lines 120–122.
- Expected: Shuffle invalidates stored `seen` previews.
- Actual: The deck is shuffled, but `s.seen` is left unchanged.
- Severity: **Major**
- Confidence: **High**

## Open questions

- Lines 103–107 choose `others[0]`, which is not always the next clockwise player, and line 153 can route reaction priority through the original actor. The canonical facts say physical priority is not hard-testable, so I leave the exact eligible-player sequence as a question rather than a scored contradiction.
- Only the drawing player’s preview is cleared at line 155. The supplied decisions explicitly address Shuffle, but do not fully specify how remembered previews should be represented after another player draws.
- Reinsertion positions exist as explicit actions, but whether their secrecy is adequately protected requires player-specific observations, which the approved facts identify as not fully verifiable.

## Coverage

Covered: setup construction, hand and deck counts, ordinary turn flow, drawing, explosion, Defuse, elimination, terminal returns, Attack, Skip, Favor, Shuffle, future preview, Nope chains, pairs, triples, five-card combinations, and discard retrieval.

Not fully covered: physical Nope timing, statistical shuffle/theft quality, social start-player selection, player-specific information views, and identity of equivalent physical copies.

Qualitatively, the basic setup and ordinary turn skeleton are sound, but several explicit interaction rules are contradicted. The most serious defect is the valid Nope-chain edge case that can crash or deadlock the engine; attacked Defuses, elimination cleanup, triple declaration, and five-card retrieval also materially change legal play.