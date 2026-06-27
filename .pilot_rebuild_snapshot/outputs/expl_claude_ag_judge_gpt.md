### 1. Score

- score: 0.86
- confidence: high

The implementation is broadly faithful: it models setup, turn order, all listed card counts/effects, Defuse, Attack/Skip, Nope parity, combos, chance, and hidden hands. Remaining issues are mostly assumptions around ambiguous timing/edge cases and some imperfect hidden-information/action-label handling rather than missing core mechanics.

### 2. Top findings

1. **severity: minor**  
   **evidence:** `see_future` stores `s.peeks[actor] = tuple(s.deck[:3])`, but `_resolve_draw` clears all peeks with `s.peeks = {}`. Rule says the player looks at the top three cards and returns them unchanged.  
   **why it matters:** The card’s effect is knowledge; a player may still remember/infer cards after one known draw, especially during an Attack with multiple turns.  
   **suggested next action:** Track observed deck-prefix knowledge more carefully, or document the simplified no-perfect-recall information model.

2. **severity: minor**  
   **evidence:** The code invents a sequential Nope polling/pass protocol in `PH_NOPE`; the rule only says Nope is always playable, can cancel another Nope, and cannot cancel Exploding Kittens/Defuse.  
   **why it matters:** The chosen reaction order and explicit `pass` actions affect the game tree and benchmarks.  
   **suggested next action:** Keep if accepted as a BoardBench convention, but add deterministic tests for odd/even Nope chains.

3. **severity: minor**  
   **evidence:** Combos are allowed over all `CARD_TYPES`, including edge cases such as Defuse/Nope and potentially Exploding Kitten if recovered; five-card combo can only take a card already in discard before the combo is played.  
   **why it matters:** The rule says all same cards can form pairs and five different cards may take any discard card, but special-card/EK and “just-played cards in discard” edge cases are unclear.  
   **suggested next action:** Clarify combo eligibility and five-card discard timing.

4. **severity: minor**  
   **evidence:** Start player is fixed as seat 0; Defuse is automatically used if held; returns are conventionally `+1/-1`.  
   **why it matters:** These are reasonable deterministic choices, but the rulebook leaves start player arbitrary, says a player “can” play Defuse, and does not define numeric returns.  
   **suggested next action:** Document as benchmark conventions or make start/Defuse choice configurable.

5. **severity: minor**  
   **evidence:** Action/render labels use internal English names like `play:skip`, `play:favor->P1`, `see_future`, and placeholder cats `cat_a..cat_e`, while the rulebook labels are German/card-title based such as Hops!, Wunsch, Mischen, Blick in die Zukunft.  
   **why it matters:** BoardBench side-by-side inspection is easier when rulebook labels are preserved.  
   **suggested next action:** Add aliases or canonical names closer to the provided rule text.

6. **severity: question**  
   **evidence:** `_explode` resets the next player to `turns_remaining = 1` even if the exploding player was resolving an Attack obligation.  
   **why it matters:** The rule does not explicitly say what happens to a second required Attack turn if the victim explodes on the first.  
   **suggested next action:** Ask for clarification or keep documented as an assumption.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | covered correctly | Deals 7 non-EK/non-Defuse cards, adds one Defuse per player, inserts `n-1` EKs, handles 2-player Defuse variant | Start player fixed to P0 as convention |
| player count and turn order | covered correctly | `Game(2..5)`, `_next_alive`, eliminated players skipped | Attack-related death edge case unclear |
| legal actions | partially covered | `draw`, single card plays, Favor targets, pair/triple/five combos, Nope reactions, Defuse insertions | Some edge restrictions/allowances are assumptions |
| state transitions | covered correctly | Fresh cloned states, discard/hand/deck updates, Attack/Skip/Shuffle/Favor/Pair/Triple/Five implemented | Nope protocol is invented but plausible |
| terminal conditions | covered correctly | `_explode` sets `PH_DONE` when one player remains; terminal has no legal actions | Matches “last alive wins” |
| scoring/returns | covered correctly as convention | `+1.0` alive winner, `-1.0` eliminated players | Rulebook has win/loss but no numeric scoring |
| rendering/action names | partially covered | Stable string action names and deterministic render | Names do not closely preserve German card labels; render is full debug truth |
| chance | covered correctly | Chance nodes for deal, deck order/shuffle, random pair steal | Large setup chance tree but rule-faithful |
| hidden information | partially covered | `information_state` hides other hands/deck and shows own hand/peeks | See-Future memory/perfect recall is simplified |
| simultaneous/reactive play | partially covered | No true simultaneous moves; Nope modeled as sequential reaction phase | Rule gives reactive timing but not exact protocol |

### 4. Unsupported assumptions or invented rules

**Mostly harmless conventions**
- Seat 0 is always the start player.
- Numeric returns use `+1/-1`.
- Unknown cat-card names are represented as `cat_a..cat_e`.
- Shuffle/setup randomness is modeled as explicit chance ordering.
- `render()` is a full debug view, not a player-visible view.

**Riskier assumptions**
- Nope uses a sequential polling and explicit `pass` protocol.
- Defuse is mandatory if held.
- See-the-Future knowledge is cleared after any draw rather than tracked with memory/inference.
- Five-card combo can only retrieve a pre-existing discard card, not necessarily one of the just-played combo cards.
- Special cards and potentially Exploding Kitten can participate in combos if they enter a hand.
- Favor/pair targets are restricted to players with cards.
- Outstanding Attack obligations disappear if the attacked player explodes.

### 5. Missing scenario tests

- Prepared 2-player state: P0 no Defuse, deck top `exploding_kitten`; action `draw` should eliminate P0 and return `[-1, 1]`.
- Prepared state: P0 has `defuse`, deck top `exploding_kitten`; actions `draw`, `insert_ek:1` should discard Defuse, reinsert EK, and advance turn.
- Attack/Skip: P0 `play:attack`; P1 should have `turns_remaining=2`; P1 `play:skip` should reduce to one remaining turn.
- Attack forwarding: P0 `play:attack`; P1 `play:attack`; P2 should owe two turns.
- Nope parity: P0 `play:attack`, P1 `nope`, P0 `nope`, then passes as needed; attack should resolve.
- Favor: P0 `play:favor->P1`; P1 `give:defuse` should transfer that card.
- Pair random steal: P0 `pair:cat_a->P1`; chance action `chance:steal:<card>` should transfer one random card type.
- Triple: P0 `triple:cat_a:defuse->P1` should transfer Defuse only if P1 has it.
- Five combo: P0 `five:defuse-nope-attack-favor-cat_a:<discard_card>` should remove five cards and retrieve from discard after Nope window.
- See Future: P0 `play:see_future` should reveal top three only in P0 information state.
- Shuffle: P0 `play:shuffle`, then `chance:order:<card>` sequence should rebuild deck and clear peeks.

### 6. Open questions for the human

- Should Defuse be optional or mandatory when a player has one?
- Should See-the-Future knowledge persist after known draws, especially during Attack-mandated multiple turns?
- Can five-card combo retrieve one of the five just-played cards, or only a card that was already in the discard pile?
- Are Defuse, Nope, and Exploding Kitten valid combo cards if present in hand?
- What happens to an outstanding Attack second turn if the attacked player explodes on the first required turn?
- Is the sequential Nope/pass protocol acceptable for benchmarking?

### 7. Machine-readable summary

```text
score: 0.86
confidence: high
critical_issues: 0
major_issues: 0
minor_issues: 5
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
