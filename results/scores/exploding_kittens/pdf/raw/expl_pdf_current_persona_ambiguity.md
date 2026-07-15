I found several genuine specification gaps, but the approved rule facts resolve most of them. The implementation follows some adjudications and contradicts others—most notably the corrected five-card retrieval rule.

## Ambiguous rules

### 1. Five-card combination: when does retrieval eligibility get determined?

- Page 2: “Wenn du 5 verschiedene Karten … spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Plausible interpretations:

  1. The five cards are discarded first, so any of those five may immediately be retrieved.
  2. The retrieval target must already be in the discard pile when the combination is declared.

- Implementation: legal targets are generated only from the pre-existing discard at [implementation.py:89](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:89). The five components are added later at [implementation.py:175](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:175), after the target has already been fixed.
- Effect: newly discarded components are not legal retrieval choices. A same-title card can appear selectable only if that title was already represented in the discard.
- Approved decision: **Yes.** FIVE-01 and the July 15 correction explicitly select interpretation 1.
- Clarification: “Discard the five component cards before choosing; any one of them may therefore be chosen from the discard immediately.”

This is no longer an unresolved ambiguity for evaluation; the implementation conflicts with the corrected approved rule.

### 2. Can special cards participate in combinations?

- Page 2: “Jetzt können ALLE gleichen Karten als Pärchen gespielt werden …” and “Wenn du 5 verschiedene Karten (jede mit einem anderen Titel) spielst …”
- Plausible interpretations:

  1. “ALLE” and “jede” include Exploding Kittens and Defuses whenever such cards legally exist in hand.
  2. Kittens and Defuses are special response cards and cannot be voluntarily used as combination components.

- Implementation: both are excluded from pairs, triples, and the five-title pool at [implementation.py:84](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:84) and [implementation.py:89](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:89).
- Effect: fewer legal combinations; a Kitten retrieved into hand cannot be used even in a same-title combination.
- Approved decision: **Yes for same-title combinations.** PAIR-01 says any two same-title cards, and FIVE-02 expressly says a retrieved Kitten may participate in same-title combinations. The general wording of FIVE-01 also supplies no special-card exclusion for five distinct titles.
- Clarification: “Any card title, including Exploding Kitten and Defuse, may be used in a combination; its printed action is ignored.”

The Kitten pair/triple exclusion directly contradicts the approved facts.

### 3. Is using a Defuse optional?

- Page 2: “Wenn du ein Exploding Kitten ziehst, kannst du eine „Entschärfung“ ausspielen, statt zu sterben.”
- Plausible interpretations:

  1. “Kannst” offers a real choice, including voluntary elimination.
  2. It merely describes the available rescue; a player possessing Defuse must use it.

- Implementation: automatically removes and discards a Defuse at [implementation.py:156](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:156); voluntary elimination is not an action.
- Effect: terminal results and elimination timing.
- Approved decision: **Yes.** DEF-01 mandates use.
- Clarification: “If you possess a Defuse when you draw a Kitten, you must play it.”

The implementation follows the adjudication.

### 4. What survives after Defusing during an Attack?

- Page 2: Attack makes the victim perform “zwei Spielzüge direkt nacheinander”; Skip says it ends only “einen der zwei Züge”; Defuse says “Dann ist dein Spielzug beendet.”
- Plausible interpretations:

  1. Defuse ends one individual turn, leaving any additional Attack turn owed.
  2. Defuse ends the player’s complete attacked turn sequence.

- Implementation: reinsertion always advances to the next player and resets `turns_left` to one at [implementation.py:136](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:136). Thus all remaining Attack obligation disappears.
- Effect: current player, remaining turns, draws, and potentially the winner.
- Approved decision: **Yes.** DEF-04 says further owed turns must still be taken.
- Clarification: “Defusing ends only the individual turn in which the Kitten was drawn; any additional Attack turns remain.”

The implementation contradicts the approved decision.

### 5. Does an Attack stack or replace an existing obligation?

- Page 2: “Spielt dein Opfer dabei selbst eine Karte „Angriff“ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Plausible interpretations:

  1. The next player owes exactly two turns; the prior remainder is replaced.
  2. The new two turns accumulate with the outstanding Attack turns.

- Implementation: sets the next player’s obligation to exactly two at [implementation.py:115](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:115).
- Effect: turn count, legal Skip requirements, and number of mandatory draws.
- Approved decision: **Yes.** ATK-02 chooses replacement.
- Clarification: “An Attack played while attacked replaces, rather than adds to, all remaining owed turns.”

The implementation follows the adjudication.

### 6. When is a triple’s requested title declared, and may it be absent?

- Page 2: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst. Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine solche Karte, hast du Pech gehabt.”
- Plausible interpretations:

  1. The actor names any title without seeing the target’s hand, before the Nope window.
  2. The title is selected after reactions, possibly from titles known to be present.

- Implementation: the initial action supplies only component title and target. After reactions, legal requests are derived directly from the target’s actual hand at [implementation.py:71](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:71). It also provides a generic “not present” action instead of allowing a named absent title.
- Effect:

  - Leaks the target’s private card titles.
  - Prevents honest blind requests for absent titles.
  - Hides the requested title from players deciding whether to Nope.

- Approved decision: **Yes.** SET-08 makes hands private, and NOPE-06 requires the requested title to be announced before reactions.
- Clarification: “Choose and announce any card title and the target before the Nope window, without inspecting the target’s hand.”

The implementation contradicts both the approved information rule and reaction timing.

### 7. Who receives Nope opportunities, and when does the chain close?

- Page 2: “Du kannst ein NÖ! auf ein anderes NÖ! legen …” and “Du kannst ein NÖ! auch spielen, wenn du nicht an der Reihe bist.”
- Plausible interpretations:

  1. Real-time play: anyone may react until the table stops responding.
  2. A deterministic priority ring gives each living player an opportunity and closes after one complete pass cycle.

- Implementation: the initial cycle starts with opponents only at [implementation.py:102](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:102). After a Nope, `_next` can include the original actor, but closure still uses the number of opponents at [implementation.py:145](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:145). Consequently, opportunity order can differ before and after the first Nope.
- Effect: which players may cancel or restore an action, reaction information, and final action resolution.
- Approved decision: **Partially.** The API convention selects deterministic clockwise opportunities and consecutive passes, but declares physical speed/priority non-hard-testable.
- Clarification: “Beginning with the next living player clockwise, every living player—including the actor—receives priority; the window closes after every living player passes consecutively since the last Nope.”

## Missing edge-case rules

### Target spends its last card during the Nope chain

- Related page 2 quotes: “Zwinge einen Mitspieler … dir eine Karte zu geben” and “eine zufällige Karte … stehlen.”
- Plausible completions:

  1. The restored action resolves without a transfer.
  2. The action becomes invalid, is retargeted, or requires some fallback.

- Implementation behavior:

  - Favor enters a phase with no legal donation action because the hand is empty.
  - Pair calls random choice on the empty hand at [implementation.py:124](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:124), which can raise an exception.

- Effect: legal-action deadlock or runtime failure.
- Approved decision: **Yes.** NOPE-07 says resolve without transfer.
- Clarification: “If the announced target has no cards when a restored action resolves, the action finishes with no transfer.”

### Fewer than three cards for “Blick in die Zukunft”

- Page 2: “Schau dir die obersten drei Karten des Spielstapels an …”
- Plausible completions: inspect all remaining cards, or treat the action as unavailable.
- Implementation: shows up to three using a slice at [implementation.py:122](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:122).
- Effect: legal actions and private information near the end of the deck.
- Approved decision: **Yes.** FUT-01 says show all remaining cards.
- Clarification: “If fewer than three cards remain, look at all of them.”

The implementation follows this decision.

## Direct contradictions, not source ambiguities

These rules are explicit enough that the alternative implementation behavior is not reasonably attributable to underspecification:

- Page 2: “Alle deine restlichen Karten und das Exploding Kitten wandern auf den Ablagestapel.” On elimination, the implementation discards only the Kitten and leaves the dead player’s hand intact at [implementation.py:159](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:159). This corrupts discard contents and later five-card retrieval availability.

- Page 2: “Misch den Spielstapel sorgfältig neu.” Approved FUT-03 says an old preview becomes stale after Shuffle. The implementation shuffles at [implementation.py:120](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_ambiguity_pw1xfyrx/implementation.py:120) without clearing any player’s `seen` record. It clears only the drawing player’s record on a later draw at line 155.

- The corrected approved five-card rule permits retrieving one of the five newly discarded components. The implementation’s pre-discard legal-action enumeration prevents that.

- Approved FIVE-02 permits a held Kitten in same-title combinations. The implementation expressly excludes it.

- Approved DEF-04 preserves further Attack turns after Defuse. The implementation discards them.

- Approved NOPE-06 requires a triple’s request before reactions. The implementation postpones it until afterward.

## Merely untestable or interface-dependent

The packet expressly leaves these outside hard rule fidelity:

- Exact physical timing and speed priority for Nope reactions.
- Probability distributions for Shuffle and random theft.
- Social start-player selection; player 0 is the approved API default.
- Which physical copy of an identical title is retrieved from discard.
- Complete secrecy of hands, deck order, reinsertion position, and previews without player-specific observation APIs.
- Internal setup counts not exposed through the minimal public interface.
- Numeric/string action encoding and display language.

The implementation’s `render` hides card identities, but `GameState` itself exposes deck, hands, and `seen`. Whether that violates secrecy cannot be settled without a specified observation boundary.

## Material-assumption summary

The implementation materially assumes that five-card targets come only from the old discard, Kittens and Defuses cannot be combination components, Defuse clears an entire Attack obligation, and triple requests may be selected after reactions using the target’s actual hand. Those assumptions are all resolved differently by the approved facts.

It correctly assumes mandatory Defuse, replacement rather than stacking for Attack-on-Attack, and “show all remaining” when fewer than three cards remain. The only substantial ambiguity intentionally left open is the exact Nope priority procedure; its current implementation is deterministic but internally asymmetric. No Judge score was emitted or modified.