# BoardBench judge reply — exploding_kittens (agentic)

### 1. Score

- `score: 0.85`
- `confidence: high`
- Justification: A thorough, faithful implementation. The setup deck-composition math is correct for every player count I checked (n=2..5, including the explicit 2-player defuse=2 box), the "play any number then draw" turn loop is right, and Attack (non-stacking, matching this rulebook's wording), Skip-vs-Attack, Nope/Doch (parity), Favor, Defuse reinsertion, and all three combos are modeled per the rule text. The rulebook's worked example (See-the-Future → Attack → Noped → Shuffle → draw) is fully reproducible. Points come off only for a handful of defensible-but-unspecified assumptions (nope polling order, auto-defuse, 2-player EK count) and the absence of bundled deterministic tests.

### 2. Top findings

1. **question/minor — Nope resolution order is an invented procedure.** The rulebook makes Nope real-time and out-of-turn ("Immer einsetzbar", "auch spielen, wenn du nicht an der Reihe bist"). The code imposes a clockwise poll that re-opens after each Nope (`_open_nope`). The *outcome* is faithful (final parity decides cancel/resolve, and every eligible player is repeatedly polled, so the achievable result set is unchanged), but precedence among multiple nopers is engine-defined, not rulebook-defined. Why it matters: edge cases decide *who* spends a Nope. Next action: document as a deliberate discretization (already partly done in the header).

2. **minor — Defuse is auto-played, removing the rulebook's optional "kannst".** `_resolve_draw` automatically plays a Defuse on an EK draw if one is held; there is no `play:defuse`-decline action. This is a dominated choice (declining = dying), so it is outcome-harmless, but it is strictly a removed decision node. Next action: acceptable for benchmarking; optionally expose a choice node if agent action-space fidelity matters.

3. **question — 2-player EK count is assumed, not stated.** The variant box only specifies "nur 2 Karten Entschärfung". The code keeps EK = n-1 = 1 for two players (`bp['exploding_kitten'] = s.n - 1`, defuse override `dd = 2 if n==2`). Defensible reading, but the rule text does not confirm the 2-player EK count. Next action: confirm with the rulebook owner.

4. **minor — Action names use English identifiers, not the rulebook's German labels.** `play:skip`, `play:attack`, `defuse`, `nope`, etc. instead of Hops!/Angriff/Entschärfung/Nö!. The generation prompt prefers rulebook labels. Round-tripping is fine (names are the actions), but the labels diverge from the source. Next action: harmless; note as a translation convention.

5. **minor — No bundled deterministic scenario tests.** Only a `__main__` smoke print exists. The benchmark value depends on testable transitions; see section 5.

6. **minor — `insert_ek:<i>` is a raw deck index, and the steal/deal/order chance action names encode hidden card identities.** The index is the natural representation of "anywhere in the pile" so it is defensible; the chance-name leakage is confined to raw action strings (the backbone itself suggests `chance:deal:<card>`) and does **not** appear in `information_state`, so the hidden-info contract holds. Next action: none required.

### 3. Rule coverage review

| rule area | status | evidence | notes |
|---|---|---|---|
| Setup / components | covered correctly | `_apply_deal`/`_finish_build`; deck = 51−7n (35 for 2p variant), 1 defuse per hand, EK=n−1, pile-defuse=(2 if n==2 else 6−n) | Verified math for n=2..5; 56-card total forces 5 cat types |
| Player count & turn order | covered correctly | `Game(num_players)` 2..5, clockwise via `_next_alive`, start=seat 0 | Start seat is a harmless convention (rulebook allows arbitrary) |
| Legal actions | covered correctly | `_play_actions` enumerates draw/single/favor/pair/triple/five; phase-specific lists | `legal_actions` only returns what `apply_action` accepts |
| State transitions | covered correctly | Attack→2 turns non-stacking; Skip ends one of two; Defuse reinsert; combos suppress card effects | Matches "zwei Spielzüge"/"überspringst nur einen" wording |
| Nope / "Doch" | partially covered | `_apply_nope`, parity in `_resolve_pending` | Outcome-faithful; polling order is engine-defined (finding 1) |
| Terminal conditions | covered correctly | `_explode` → DONE when `sum(alive)==1`; EK=n−1 guarantees exactly one survivor | No draws possible; terminal has no legal actions |
| Scoring / returns | covered correctly (convention) | `returns`: +1 survivor, −1 each eliminated | Numeric mapping invented (rulebook only says win/lose); one value per player |
| Rendering / action names | covered correctly | `render` deterministic full-truth debug view; identity `action_to_name`/`name_to_action` | Round-trips exactly; labels English not German (finding 4) |
| Chance handling | covered correctly | DEAL/BUILD/STEAL chance nodes; `chance_outcomes` weights sum to 1, mirror `legal_actions` | No hidden RNG; shuffle re-orders via BUILD |
| Hidden information | covered correctly | `information_state` hides other hands + deck order; reveals sizes/discard/own peek | Matches "Anzahl jederzeit nachzählen"; render documented as non-player view |
| Simultaneous moves | n/a (modeled sequentially) | Nope window only | Rulebook has no true simultaneous commit; sequential polling is appropriate |

### 4. Unsupported assumptions or invented rules

- **Harmless conventions:** start player = seat 0; returns +1/−1; cat cards labelled `cat_a..cat_e` (the 56-card total forces exactly 5 types; only same/different title is mechanically used); English action identifiers; modeling deal/shuffle/steal as explicit chance trees.
- **Defensible-but-unconfirmed:** 2-player EK = 1 (rulebook silent — finding 3); Triple/wish cannot name `exploding_kitten` (`WANTED_TYPES` excludes EK — practically unreachable in a hand, so low-risk).
- **Risk-bearing (low):** auto-defuse removes the optional decline (finding 2); engine-defined Nope precedence (finding 1). Both are outcome-faithful but are decisions the rulebook does not make.

### 5. Missing scenario tests

- **Setup composition (per n):** force any DEAL+BUILD chance sequence; assert every hand = 8 cards incl. exactly one `defuse`; `len(deck)` = 51−7n (35 for n=2); EK-in-deck = n−1; defuse-in-deck = 2 (n=2) else 6−n.
- **See-the-Future:** set deck top `[attack,skip,favor]`; `play:see_future`; assert `information_state` peek; then `draw` adds `attack`.
- **Attack two-turns:** `play:attack` (all `pass`) → current=P1, `turns_remaining=2`; `draw`,`draw` → control reaches P2.
- **Skip under Attack:** with `turns_remaining=2`, `play:skip` → same player, `turns_remaining=1`; second `play:skip` → next player.
- **Nope cancel + Doch:** `play:attack`,`nope`,`pass...` → fizzles, actor still current; then `play:attack`,`nope`,`nope`(Doch),`pass...` → resolves (P1 gets 2 turns).
- **Defuse reinsert:** deck top = `exploding_kitten`, holder has `defuse`; `draw` → DEFUSE; `insert_ek:0`; assert turn ended and next drawer hits the EK.
- **Lethal draw / terminal:** holder without defuse draws EK → eliminated; in 2p reduce to one alive → `is_terminal`, `legal_actions==[]`, `returns` exactly one +1 and rest −1.
- **Favor / Pair / Triple / Five:** `play:favor->P1` then `give:X` transfers; `pair:cat_a->P1` → STEAL chance moves a card; `triple:cat_a:skip->P1` transfers iff target holds `skip`; `five:<5 titles>:nope` moves `nope` from discard.
- **Round-trip:** for sampled legal actions across all phases, assert `name_to_action(action_to_name(a)) == a`.

### 6. Open questions for the human

- 2-player variant: how many Exploding Kittens (rulebook gives only the 2-defuse rule)?
- May a Triple/wish name an Exploding Kitten or a Defuse? (Code excludes EK.)
- Is there an intended precedence when several players could Nope, or is it genuinely free-for-all (affects only who spends a Nope, not the result)?
- Is declining to play a held Defuse ever legal/intended, or is auto-defuse acceptable?

### 7. Machine-readable summary

```text
score: 0.85
confidence: high
critical_issues: 0
major_issues: 0
minor_issues: 6
needs_rulebook_clarification: true
needs_code_change: false
needs_more_tests: true
```
