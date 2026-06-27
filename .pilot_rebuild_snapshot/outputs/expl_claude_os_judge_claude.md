# Exploding Kittens (oneshot) — LLM judge review

### 1. Score

- `score: 0.82`
- `confidence: medium`

The implementation is broad and unusually faithful: correct component counts (derivable to the stated 56), correct setup including the two-player Defuse variant, the "play-any-number-then-draw" turn loop, Nope/Doch parity, non-stacking Attack, skip/attack-under-attack accounting, explicit chance nodes (no hidden RNG), a clean hidden-info split, and stable terminal/returns. The main rule-fidelity gap is partial support for Defuse reinsertion placement, plus a handful of documented assumptions where the rulebook is genuinely silent or ambiguous (combo eligibility of Defuse/Nope, optional-vs-forced defuse, death-during-attack). No critical or terminal-logic bugs were found.

### 2. Top findings

**[major] Defuse reinsertion placement is only partially representable.**
Rulebook: "Lege ... das Exploding Kitten zurück in den Spielstapel, und zwar geheim an eine Stelle deiner Wahl" and the explicit "Lege das Exploding Kitten ganz oben auf den Spielstapel ... dem nächsten Spieler eins auswischen." The `INSERT` phase offers `insert:top`, `insert:pos<k>` (only within the already-revealed `deck_known` prefix), and `insert:random` (drop into the unordered `deck_pool`). Precise placement at an arbitrary unseen depth (notably exact bottom) cannot be expressed. The rulebook's explicitly named placements (top; "secretly somewhere") *are* covered, but bottom-burying is a strong strategic lever that benchmark agents cannot use. *Next action:* confirm whether coarse placement is acceptable, or extend the deck model to allow indexed insertion into the unknown region.

**[question] Optional defuse exposes a never-rational action.**
`DEFUSE` phase returns both `play_defuse` and `explode` even when a Defuse is in hand. This is faithful to "kannst du eine Entschärfung ausspielen, statt zu sterben," but `explode` then discards the still-held Defuse — a trap with no upside. *Next action:* decide force-vs-optional defuse.

**[question] Defuse and Nope are eligible as combo material.**
`_play_actions` builds pairs/threes from any title with enough copies and fives from any 5 distinct titles, so `pair:defuse:p1`, `pair:nope:p2`, or a five including `defuse` are legal. Rulebook: "Jetzt können ALLE gleichen Karten als Pärchen gespielt werden ... für alle Karten mit dem gleichen Titel." Literal text supports it; designer intent may exclude the special Defuse/Nope. *Next action:* clarify combo eligibility.

**[minor] See-the-Future private memory is dropped too eagerly.**
`_do_draw` sets `last_seen = None` on *every* draw, so a player who peeked three cards "forgets" the still-valid remaining cards after the next single draw. Conservative (never leaks), but loses information fidelity. *Next action:* trim the seen prefix instead of clearing it.

**[minor] Death-during-attack voids the remaining turn (rulebook silent).**
`_explode` resets `next_player_turns = 1`; if an attacked player explodes on the first of two turns, the second turn is discarded rather than carried. The rulebook does not address this; flag as an assumption.

**[minor/testability] Five-combo enumeration is combinatorial.**
`itertools.combinations(distinct, 5) × discard-types` can produce large action sets in rich hands. Not a correctness bug, but it complicates exhaustive deterministic checks.

### 3. Rule coverage review

| rule area | status | evidence | notes |
|---|---|---|---|
| Setup / components | covered correctly | `FULL_COUNTS` totals 56; per-type counts match the "beispielzug" list; 5 cat types derived (56−36)/4 | cat-type count is forced by arithmetic, not invented |
| Deck build (EK n−1, Defuse rule, 2p variant) | covered correctly | `_finalize_setup`: `ek = np-1`, `defuse_into_deck = 2 if np==2 else 6-np` | card-conservation checks out for n=2..5 |
| Player count / turn order | covered correctly | `2 <= num_players <= 5`; `_next_living` clockwise; start fixed to player 0 | fixed starting player is a harmless convention |
| Turn structure (play-any-then-draw) | covered correctly | `_play_actions` returns `draw` + plays; draw/skip/attack end the turn | matches "Passen oder spielen, dann ziehen" |
| Legal actions | covered correctly | solo (Attack/Skip/Shuffle/Future), Favor(+target), pair/three/five; cats only in combos; Defuse/Nope reactive | `legal_actions ⊆ apply_action` holds per phase |
| Attack (non-stacking, victim re-attack) | covered correctly | `_resolve_pending` sets `next_player_turns = 2` then `_advance_turn` | matches "der nächste Spieler muss zwei Spielzüge" |
| Skip (one of two turns) | covered correctly | `_consume_turn` decrements `turns_to_take` | matches "zweimal Hops!" rule |
| Nope / Doch | covered correctly | parity via `nope_count % 2`; off-turn responders; EK/Defuse excluded | sequential clockwise polling is a reasonable abstraction |
| Favor (target chooses) | covered correctly | `FAVOR_GIVE`, `cur = target` | not a random steal — correct |
| Pair / Three / Five | covered correctly | random steal as `STEAL_CHANCE`; three names a type; five takes from discard | Defuse/Nope eligibility is the open question |
| See-the-Future | covered correctly | `FUTURE_CHANCE` materializes top-3; `information_state` reveals only to peeker | memory-clear-on-draw is over-eager (minor) |
| Defuse / reinsertion | partially covered | `DEFUSE`→`INSERT`; top/revealed-pos/random only | arbitrary unseen depth not representable (major) |
| Terminal / win | covered correctly | `_explode` → `GAMEOVER` when `sum(alive) <= 1`, last alive wins | matches "nur noch ein Spieler ... der Gewinner" |
| Scoring / returns | covered correctly | winner +1, others −1, non-terminal all 0 | one value per player; stable |
| Chance handling | covered correctly | deal/draw/future/steal as explicit chance; probs sum to 1, match `legal_actions` | no hidden RNG |
| Hidden information | covered correctly | `render` = full debug; `information_state` = own hand + public | no leak via legal actions at chance/give nodes |
| Rendering / action names | covered correctly | canonical strings, card labels + `p<n>`, identity round-trip | no signed coords; no index-only names |
| Simultaneous moves | n/a | Nope reactions serialized | acceptable |

### 4. Unsupported assumptions or invented rules

- Harmless conventions: starting player = 0; sequential per-player dealing (distribution-equivalent to round-robin); fixed canonical card/cat identifiers.
- Derived, not invented: 5 cat types (forced by 56-total minus the listed per-type counts).
- Risky/uncertain (rulebook ambiguous):
  - Defuse/Nope usable as combo cards (literal "alle Karten").
  - `explode` offered as a legal choice when a Defuse is available.
  - Death during an attack voids the remaining turn rather than transferring it.
  - Five-combo blocked when discard has no non-EK card; EK excluded from five-take ("beliebige Karte").
  - Deck modeled as ordered-known prefix + unordered pool, which constrains Defuse placement granularity (see major finding).

### 5. Missing scenario tests

The file ships only a greedy smoke rollout. Suggested deterministic checks (action-name sequences):

- Setup invariants per n=2..5: each hand size 8 after deal; deck has exactly `n-1` EK and the expected Defuse count; total cards conserved = 56; two-player case has 1 EK + 2 Defuse in deck.
- EK without Defuse: `chance:draw:exploding_kitten` → exploder's hand + EK on discard, `alive=0`, turn advances.
- EK with Defuse: `... → play_defuse → insert:top` then verify the *next* player draws that EK.
- `insert:top` while under attack (`turns_to_take=2`): same player draws the EK again on their second turn.
- Attack non-stacking: A `play:attack` → B `turns_to_take=2`; B `play:attack` → C `turns_to_take=2`, B no longer current.
- Skip under attack: two `play:skip` needed to end both turns.
- Nope parity: `play:attack` → `play_nope` (canceled, owner continues) vs `play:attack` → `play_nope` → `play_nope` (Doch, attack resolves).
- Favor: target's `give:<card>` is a chooseable decision, not a chance node.
- Pair: `pair:cat_a:p1` → `STEAL_CHANCE` distribution equals target's hand multiset.
- Three: name a type the target has (forced give) vs lacks (no effect).
- Five: with non-empty discard, `five:...:take:<d>` removes exactly that discard card; with empty discard, no five action is offered.
- See-the-Future: `information_state` `seen_top` set for the peeker only; other players' views unchanged.
- Round-trip: `name_to_action(action_to_name(a)) == a` over a sampled action set including a five-combo.
- Terminal: at `GAMEOVER`, `legal_actions == []` and `returns` sums to `2 - n`.

### 6. Open questions for the human

1. Is coarse Defuse placement (top / revealed-prefix positions / random-into-unknown) acceptable, or must arbitrary unseen-depth placement (e.g., exact bottom) be representable?
2. Do "alle gleichen Karten" combos include Defuse and Nope, or should those be excluded from pair/three/five?
3. When an attacked player explodes on the first of two turns, is the remaining turn voided (current behavior) or passed on?
4. Should declining a held Defuse (`explode`) remain legal, or should defusing be forced?
5. For the five-combo, may EK be taken from the discard, and may a player take back a card they just played into the same combo?

### 7. Machine-readable summary

```text
score: 0.82
confidence: medium
critical_issues: 0
major_issues: 1
minor_issues: 5
needs_rulebook_clarification: true
needs_code_change: false
needs_more_tests: true
```
