## Review result

The implementation makes nine material assumptions where the publisher rulebook is silent. All nine are already resolved by the approved fact inventory/human decisions, so these choices should not be treated as implementation defects. I found no contradiction among the assigned canonical sources and implementation.

### Missing rules resolved by approved decisions

1. **Card identities — `6N-M-CARD-IDENTITIES`**

   - Page 1: “Inhalt: 104 Spielkarten.”
   - Plausible interpretations: the deck is numbered 1–104 once each; or it contains some other set of 104 numbered cards, possibly with duplicates or gaps.
   - Implementation: constructs exactly `range(1, 105)` at [implementation.py:58](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:58).
   - Effect: determines every possible hand, row, reserve card, legal card action, and placement comparison.
   - Approved resolution: **Yes.** The approved user observation specifies one copy of every integer 1–104.
   - Clarification: “The deck contains exactly one card of each value from 1 through 104.”

2. **Complete bullhead inventory — `6N-M-BULL-INVENTORY`**

   - Page 2: “Auf jeder Karte sind zwischen den Zahlen Hornochsenköpfe abgebildet.”
   - Plausible interpretations: all cards outside the listed special categories carry one bullhead; or their printed counts require a separate component inventory and cannot be inferred from the text.
   - Implementation: assigns 55→7, other repeated digits→5, other multiples of 10→3, other multiples of 5→2, and all remaining cards→1 at [implementation.py:25](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:25).
   - Effect: changes capture penalties, cumulative scores, match duration, winners, and returns.
   - Approved resolution: **Yes.** The approved component observation supplies that exact exhaustive inventory.
   - Clarification: “Every card not covered by the 55, repeated-digit, multiple-of-10, or multiple-of-5 rules is worth one bullhead.”

3. **Digital commitment protocol — `6N-M-COMMIT-PROTOCOL`**

   - Page 1: “Alle Spieler legen verdeckt eine Karte … Erst dann, wenn der Letzte sich entschieden hat, werden die Karten aufgedeckt.”
   - Plausible interpretations: players submit sequentially in seat order with identities hidden and no undo; or commitments may arrive in any order and remain changeable until everyone locks in.
   - Implementation: exposes actions only for `current_player`, beginning with player 0 ([implementation.py:96](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:96)); removes each committed card immediately, advances to the first uncommitted seat, and reveals after the final commitment ([implementation.py:160](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:160)). There is no undo action.
   - Effect: determines who may act, submission order, whether commitments can be revised, and when information becomes public.
   - Approved resolution: **Yes.** The approved decision is private, seat-ordered commitments.
   - Clarification: “Players submit once per round in ascending seat order; a submitted card cannot be changed, and its identity remains hidden until every player has submitted.”

4. **Tied winners — `6N-M-TIE-WINNER`**

   - Page 2: “Sieger wird der Spieler, der die wenigsten Hornochsen besitzt.”
   - Plausible interpretations: every player tied for the lowest total wins; or a tie-break selects one winner.
   - Implementation: records every player whose total equals the minimum at [implementation.py:147](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:147).
   - Effect: changes terminal winners and numeric returns.
   - Approved resolution: **Yes.** Shared winners were explicitly approved.
   - Clarification: “If several players share the lowest cumulative score, all of them are winners.”

5. **Randomness and reset lifecycle — `6N-M-RNG-RESET`**

   - Page 1: “Mischen Sie alle Karten.”
   - Plausible interpretations: use nondeterministic physical-style shuffling on every deal; or use a reproducible seeded shuffle whose generator continues across games and resets on a fresh initial state.
   - Implementation: uses a defined seeded generator and Fisher–Yates-style shuffle at [implementation.py:47](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:47). An omitted seed becomes runtime seed 0 ([implementation.py:75](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:75)); later games continue the stored generator state.
   - Effect: determines deals, reproducibility, replay/reset behavior, and therefore all downstream states.
   - Approved resolution: **Yes.** Strict seeded runtime/reset behavior was approved.
   - Clarification: “Shuffles use the specified deterministic seeded generator; each new game continues its state, while creating a fresh initial state resets it to the configured seed.”

6. **Unsupported player counts — `6N-M-INVALID-PLAYERS`**

   - Page 1: “Spieler: 2–10 Personen.”
   - Plausible interpretations: reject all values outside 2–10; or permit/degrade unsupported counts, clamp them, or substitute a default.
   - Implementation: defaults an omitted count to two and raises `ValueError` for any explicitly supplied value not represented by an integer from 2 through 10 at [implementation.py:38](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:38).
   - Effect: determines whether an initial state can exist and which setup/legal-action spaces are reachable.
   - Approved resolution: **Yes.** Digital rejection outside the supported range was approved.
   - Clarification: “Omitting the player count selects two players; every explicit count other than an integer from 2 through 10 is invalid.”

7. **Player-specific observations — `6N-M-OBSERVATION`**

   - Page 1: “Alle Spieler legen verdeckt eine Karte von ihren Handkarten vor sich auf den Tisch.” Page 2 also says captured cards are placed face down.
   - Plausible interpretations: each player sees only their own hand and captured identities while seeing opponent counts/status; or all digital state, including opponent hands and captured identities, is observable.
   - Implementation: exposes `own_hand` and `own_captured`, but only hand size, captured count, and score totals for opponents at [implementation.py:351](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:351). Commitment status is public; revealed cards become public.
   - Effect: changes strategic information, legal decision inputs, and hidden-information integrity.
   - Approved resolution: **Yes.** Opponent hands and captured-card identities must remain hidden.
   - Clarification: “A player observes their own hand and captured cards; for opponents they observe only hand size, capture count, scores, and whether a card has been committed.”

8. **Pending low-card choice — `6N-M-LOW-PENDING`**

   - Page 2: a player whose card fits no row “muss alle Karten einer beliebigen Reihe nehmen.”
   - Plausible interpretations: pause ordered resolution and ask that card’s owner to choose; or automatically choose a row—possibly the lowest-penalty row suggested by the nonbinding tip—and continue.
   - Implementation: enters `choose_row`, gives that player four row-choice actions, stores later revealed cards as pending, and resumes afterward at [implementation.py:113](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:113) and [implementation.py:173](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:173).
   - Effect: changes available legal actions, phase/current actor, intermediate state, row contents, captures, and later placements.
   - Approved resolution: **Yes.** An explicit pending row-choice phase was approved.
   - Clarification: “Ordered resolution pauses when a low card occurs; its owner chooses any row, after which unresolved revealed cards continue in ascending order against the updated rows.”

9. **Numeric environment returns — `6N-M-RETURNS`**

   - Page 2: “Sieger wird der Spieler …”
   - Plausible interpretations: return +1 to winners and −1 to everyone else; or return score-derived utilities, zero-sum values, or only a winner identifier.
   - Implementation: returns zero before termination and +1/−1 at termination at [implementation.py:187](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:187).
   - Effect: changes the terminal result exposed to agents/evaluators, though not physical gameplay.
   - Approved resolution: **Yes.** Terminal +1/−1 returns were approved.
   - Clarification: “Before match termination every player’s return is 0; afterward each winner receives +1 and every non-winner receives −1.”

## Ambiguous rule

`6N-A-TEN-PLAYER-REST` is explicitly classified as non-material.

- Page 1: “Der Kartenstapel, der jetzt noch übrig ist, wird … beiseite gelegt.”
- With ten players, 100 cards are dealt and four start rows, so plausible readings are that an empty reserve is valid or that “remaining stack” implicitly assumes fewer than ten players.
- The implementation permits ten players and stores an empty reserve at [implementation.py:60](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_ambiguity_k64z8wo1/implementation.py:60).
- This affects only reserve representation, not legal actions or results.
- The approved inventory resolves the operational behavior through the reserve formula and reports no unresolved material question.
- Clarification: “At ten players no cards remain in the reserve; an empty reserve is valid.”

## Contradictory rules

None found. The component supplement is expressly limited to card identity and printed bullhead inventory and does not override gameplay rules.

## Merely untestable rule

`6N-C-TIP-NONBINDING` is clear but intentionally non-testable: page 2 says a player “wählt in der Regel die Reihe mit den wenigsten Minuspunkten.” This is strategic advice, not a mandatory row-selection rule. The implementation correctly leaves all four rows legal during a low-card choice.

## Material-assumption summary

The implementation depends on nine source-absent digital/component assumptions: exact card identities, exhaustive bullhead values, ordered non-revisable commitments, shared ties, deterministic seeded resets, invalid-player rejection, private observations, a pending low-card choice phase, and +1/−1 returns. Every one is explicitly covered by the approved facts or component observation. Consequently, there is no unresolved material source ambiguity and no ambiguity-based implementation defect to report. The neutral Judge score was neither emitted nor modified.