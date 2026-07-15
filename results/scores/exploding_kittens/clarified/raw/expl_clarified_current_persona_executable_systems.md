## Critical/major findings

None identified within the supplied canonical materials and implementation.

The reviewed implementation correctly covers the principal executable boundaries:

- Setup counts and dealing: `SET-01`–`SET-10`, [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_expl_clarified_current_executable_systems_5s2u4cki/implementation.py:55).
- Explicit targets, requested titles, donations, retrievals, and reinsertion positions: `FAV-01`, `TRI-01`, `FIVE-01`, `DEF-03`, lines 78–120 and 122–145.
- Clockwise NÖ!/DOCH! opportunities with announced parameters and consecutive-pass closure: `NOPE-01`–`NOPE-07`, lines 229–279.
- Replacement rather than stacking of Attack obligations, one-turn Skip consumption, Defuse preserving further owed turns, and elimination cancelling remaining turns: `ATK-01`–`ATK-03`, `SKIP-01`–`SKIP-02`, `DEF-04`, lines 195–227 and 281–296.
- Short Future previews and Shuffle invalidation: `FUT-01`–`FUT-03`, lines 286–290.
- Seeded Shuffle and random Pair theft: `SHUF-01`, `PAIR-01`, lines 56–66 and 303–309.
- Immediate terminal transition and `+1/-1` returns: `TERM-01`–`TERM-02`, lines 147–154 and 218–227.

## Source gaps

- Empty-deck behavior is not independently defined. The rulebook says, page 1, “Keine Sorge, der Spielstapel wird nie leer,” and valid play preserves enough Kittens to force elimination or reinsertion. Consequently, the exception at lines 203–205 is unreachable from internally generated valid states. Its behavior for a manually malformed fixture is not a demonstrated rules defect.
- Three cat-card titles are represented by distinct placeholder names at lines 17–22 because the text extraction does not supply their printed titles. Exact action encoding and display language are explicitly evaluator interface choices, so this is not a rule-fidelity defect.

## Evaluator questions

- `GameState.hands` and `GameState.deck` are omniscient internal structures, while `render()` hides other hands and the deck order at lines 156–169. `SET-08`, `SET-09`, `FUT-02`, and the approved ambiguity note say secrecy cannot be fully verified without player-specific observations. Any hidden-information test should therefore evaluate `render()` or a defined observation boundary, not direct internal-state inspection.
- Future knowledge is cleared whenever a turn ends or a card is drawn. This removes current-top preview metadata but does not model a player’s historical memory. The canonical facts explicitly require invalidation after Shuffle (`FUT-03`), but do not require persistent belief-state tracking after ordinary public draws.

## Deterministic regression candidates

1. For each player count 2–5 and a fixed seed, assert eight starting cards per player, exactly one starting Defuse each, `players - 1` deck Kittens, and two extra deck Defuses only at two players.
2. Construct an attacked player with `turns_left=2`; resolve one Skip and assert the same player remains active with one turn left.
3. In the same state, resolve Attack and assert the next living player owes exactly two turns, with no stacking of the old obligation.
4. Draw a Kitten while attacked and holding Defuse; require an explicit insertion action, preserve unrelated deck-card order, then assert the same player retains one owed turn.
5. Eliminate an attacked player with two turns left; assert remaining obligations disappear and play advances clockwise unless the transition is terminal.
6. Announce Favor with a one-card target; have that target play its card as NÖ!, restore the Favor with another NÖ!, close the window, and assert resolution completes without entering an empty donation phase.
7. Announce Pair against a one-card target and repeat the same last-card NÖ!/DOCH! sequence; assert no theft and no random-selection error.
8. Announce a Triple with requested title `Exploding Kitten`; verify transfer when present and no transfer when absent.
9. Play a five-distinct-title combination and retrieve one of its five just-discarded components; assert exactly four components remain discarded.
10. Retrieve an Exploding Kitten from discard with a five-card combination; assert it enters the hand without explosion and cannot be played singly.
11. Resolve Future with decks of lengths 0, 1, 2, and 3; assert the private preview is respectively 0, 1, 2, or 3 cards without changing deck order.
12. Resolve Future followed by Shuffle using a fixed seed; assert the stored preview is cleared and the deck multiset is unchanged.
13. Close a reaction chain only after one full clockwise run of consecutive passes; after any NÖ!, assert the pass count resets.
14. Eliminate the penultimate player and assert terminal state, no legal actions, sole-survivor `+1`, and every eliminated player `-1`.