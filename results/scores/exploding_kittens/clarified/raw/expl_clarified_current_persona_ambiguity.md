Reviewed only [canonical_rulebook.txt](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/canonical_rulebook.txt), [canonical_rulefacts.md](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/canonical_rulefacts.md), and [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py). No Judge score was emitted or modified.

## Missing or unresolved specifications

### 1. May a powerless Cat card be played singly?

- Page 1: “Wähle eine deiner Handkarten aus, lege sie OFFEN auf den Ablagestapel und befolge ihre Anweisung.”
- Page 2: “Einzeln sind diese Karten machtlos.”
- Plausible interpretations:
  1. A Cat card may be played singly; it is discarded and has no effect.
  2. “Powerless” means it has no legal single-card play and may only be used in combinations.
- Implementation choice: interpretation 2. Main-phase single-card actions are generated only for Skip, Attack, See the Future, Shuffle, and separately Favor; Cat cards are absent at [implementation.py:95](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:95).
- Effect: changes legal actions, hand/discard state, whether a reaction window opens, and the ability to shed cards without ending the turn.
- Approved decision: none expressly resolves singleton Cat legality.
- Clarification: “Katzen-Karten dürfen nicht einzeln ausgespielt werden; sie dürfen nur als Bestandteil einer Kombination gespielt werden.”

### 2. May a Triple target an empty-handed player?

- Page 2: “Wie ein Pärchen, außer dass du dir eine Karte von dem Mitspieler wünschen darfst.”
- Page 2: “Besitzt er solch eine Karte, muss er sie dir geben. Hat er keine solche Karte, hast du Pech gehabt.”
- Plausible interpretations:
  1. Like a Pair, the target must hold at least one card.
  2. Any living opponent is legal; an empty hand simply cannot contain the requested title.
- Implementation choice: interpretation 2. Triple targets use `_living_others`, unlike Favor and Pair, which use `_targets_with_cards`, at [implementation.py:99](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:99), [implementation.py:105](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:105), and [implementation.py:108](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:108).
- Effect: changes legal actions. It can also consume three cards and provoke NÖ! responses despite being incapable of transferring a card.
- Approved decision: TRI-01/02 does not expressly impose or reject a nonempty-target condition.
- Clarification: “Ein Drilling darf [auch / nicht] gegen einen Mitspieler ohne Handkarten angekündigt werden.”

### 3. How long should See the Future information remain available?

- Page 2: “Schau dir die obersten drei Karten des Spielstapels an und lege sie zurück, ohne deren Reihenfolge zu verändern.”
- Page 2: “Zeige diese Karten bloß nicht deinen Mitspielern.”
- Plausible interpretations:
  1. Looking is a one-time event; the player must remember the cards.
  2. A digital implementation should continue displaying the known order until a draw, insertion, or shuffle invalidates it.
- Implementation choice: stores the preview during the current turn but clears it whenever an individual turn ends, including Skip or Attack even if the deck did not change. See [implementation.py:165](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:165), [implementation.py:195](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:195), and [implementation.py:287](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:287).
- Effect: private information presentation, but not deck state or legal actions.
- Approved decision: FUT-03 says a Shuffle invalidates an earlier preview, but does not say whether unchanged information must remain displayed across turns. The facts also acknowledge that secret information is not fully testable.
- Clarification: “Die Vorschau wird nur einmal angezeigt” or “Die Vorschau bleibt für diesen Spieler sichtbar, bis sich die Reihenfolge des Spielstapels ändern kann.”

## Printed ambiguities already resolved by approved decisions

### 4. Optional versus mandatory Defuse

- Page 2: “Wenn du ein Exploding Kitten ziehst, kannst du eine ‘Entschärfung’ ausspielen, statt zu sterben.”
- Plausible interpretations: the player may decline and die, or possession of Defuse requires its use.
- Implementation: automatically consumes one Defuse and enters insertion at [implementation.py:212](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:212).
- Effect: legal choices, elimination, discard state, and possibly the winner.
- Approved decision: DEF-01 expressly requires Defuse and forbids voluntary elimination.
- Clarification: “Besitzt du eine Entschärfung, musst du genau eine davon benutzen.”

### 5. Attack debt, counter-Attack, Defuse, and elimination

- Page 2: “Der nächste Spieler muss zwei Züge machen.”
- Page 2: “Spielt dein Opfer dabei selbst eine Karte ‘Angriff’ aus, ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.”
- Page 2, Defuse: “Dann ist dein Spielzug beendet.”
- Plausible interpretations include accumulating Attack obligations versus replacing them, Defuse ending all owed turns versus one individual turn, and remaining turns passing onward versus disappearing after elimination.
- Implementation: Attack replaces the recipient’s obligation with exactly two at [implementation.py:293](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:293); Skip/Defuse consume one turn through `_end_one_turn`; elimination resets the next player to one turn.
- Effect: active player, `turns_left`, draw obligations, elimination timing, and terminal outcome.
- Approved decision: ATK-02, ATK-03, DEF-04, and SKIP-02 expressly resolve all of these choices.
- Clarification: the binding clarifications 3–5 and 8 already provide suitable language.

### 6. See the Future with fewer than three cards

- Page 2: “Schau dir die obersten drei Karten des Spielstapels an.”
- Plausible interpretations: the action is unavailable/undefined with fewer than three, or it reveals every remaining card.
- Implementation: Python slicing reveals up to three, hence all remaining cards, at [implementation.py:287](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:287).
- Effect: legal action and private information.
- Approved decision: FUT-01 expressly selects “show all remaining cards.”
- Clarification: “Liegen weniger als drei Karten im Stapel, sieh dir alle verbleibenden Karten an.”

### 7. Five-card retrieval ordering

- Page 2: “Wenn du 5 verschiedene Karten … spielst, darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.”
- Plausible interpretations:
  1. Choose only from cards that were already discarded.
  2. Discard the five components first, then choose, allowing immediate retrieval of a component.
- Implementation: includes both the previous discard and the five announced cards in the retrieval choices at [implementation.py:113](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:113) and removes the selected card at [implementation.py:318](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:318).
- Effect: legal retrievals and final hand/discard composition.
- Approved decision: FIVE-01 and the July 15 adjudication correction expressly select interpretation 2.
- Clarification: “Lege zuerst alle fünf Karten ab; wähle danach aus dem nun entstandenen Ablagestapel.”

### 8. Empty-handed Favor and Pair targets

- Page 2, Favor: “Zwinge einen Mitspieler deiner Wahl, dir eine Karte zu geben.”
- Page 2, Pair: “um einem Mitspieler eine zufällige Karte zu stehlen.”
- Plausible interpretations: empty-handed opponents remain legal but yield nothing, or they are illegal targets.
- Implementation: excludes empty-handed targets for both at [implementation.py:99](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:99) and [implementation.py:105](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:105).
- Effect: legal actions and whether cards may be discarded for a guaranteed no-effect action.
- Approved decision: FAV-01 and PAIR-01 expressly make those targets illegal.
- Clarification: “Als Ziel ist nur ein lebender Mitspieler mit mindestens einer Handkarte zulässig.”

### 9. NÖ! timing, priority, and announcement completeness

- Page 2: “Du kannst ein NÖ! auch spielen, wenn du nicht an der Reihe bist.”
- Page 2, Five: “Nicht trödeln, sonst hält dich noch jemand mit einem NÖ! von deinem Vorhaben ab.”
- Plausible interpretations include unrestricted real-time interruption, a reaction opportunity in turn order, choosing targets/results before the reaction, or choosing them only after the action survives.
- Implementation: every announced action enters a clockwise reaction phase; consecutive passes close the chain at [implementation.py:229](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:229), [implementation.py:258](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:258), and [implementation.py:272](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:272). Targets, requested titles, and Five retrievals are recorded before that phase.
- Effect: legal reactions, information disclosed, reaction-card expenditure, and transfers.
- Approved decision: the interface convention and NOPE-06/07 resolve the digital ordering, including the case where a target spends its last card during the chain.
- Clarification: binding clarifications 18, 23, and 24 already supply suitable language.

## Contradictory rules

No material unresolved contradiction was found. In particular, the rulebook’s deck-nonempty assurance remains consistent with discard retrieval of a Kitten: every discarded Kitten originally accompanied an elimination, while the draw pile retains one fewer Kitten than the number of living players.

The apparent tension between “choose one of your hand cards” and singleton Cat cards being “powerless” is an ambiguity about legality, not a direct logical contradiction.

## Merely untestable or interface-dependent

These do not presently establish rule defects:

- Real-time physical NÖ! priority: replaced by the approved clockwise protocol.
- Exact Shuffle and random-theft distributions: deliberately not hard-specified.
- Secret hands, insertion position, and preview confidentiality: not fully verifiable through a single global rendering interface.
- Which physical copy of a duplicate discard title is retrieved: behaviorally equivalent.
- Social start-player selection: replaced by approved player 0.
- Exact action strings, encoding, and display language: approved interface choices.
- The empty-deck branch at [implementation.py:204](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_ambiguity_cdj5dc_z/implementation.py:204) is defensive code for a state the canonical valid-game invariant says is unreachable, not a specified terminal result.

## Material-assumption summary

The implementation’s material unresolved assumptions are:

- Cat cards cannot be played singly.
- A Triple may target any living opponent, including an empty-handed one.
- See the Future is treated as transient displayed information and is forgotten by the engine when the individual turn ends, even if the deck order did not change.

Its other consequential choices—mandatory Defuse, replacement rather than accumulation of Attack debt, one-turn Skip/Defuse consumption, empty-target restrictions for Favor/Pair, Five self-retrieval, and deterministic NÖ! windows—are supported by approved human adjudications.