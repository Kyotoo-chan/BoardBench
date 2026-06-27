### 1. Score

score: 0.70  
confidence: medium

The implementation is playable and covers the main loop, player elimination, Defuse handling, named action cards, Nope windows, and combinations. The biggest fidelity gap is that setup and shuffle randomness are replaced by deterministic or small artificial chance abstractions, and several physical hidden-choice/random-choice rules are simplified. These are documented, but they affect benchmark behavior for a card game whose rulebook relies heavily on shuffled hidden information.

### 2. Top findings

- severity: major  
  evidence: Rulebook says the deck is shuffled during setup and by `Mischen`; code uses a canonical setup and `Mischen` offers only `identity`, `reverse`, rotations, and `by_title`.  
  why it matters: Draw order and uncertainty are central to gameplay; limited shuffle outcomes can make strategy and rollouts unrepresentative.  
  suggested next action: Model setup and shuffle as broader chance nodes, or explicitly mark this as a reduced deterministic benchmark variant.

- severity: major  
  evidence: Rulebook says an Exploding Kitten is returned “geheim an eine Stelle deiner Wahl”; code exposes `insert_exploding_kitten:posN` as an explicit legal action.  
  why it matters: The action is correct mechanically, but the public full-state API/render reveals the chosen hidden position unless callers use `information_state`.  
  suggested next action: Keep full debug render if needed, but ensure benchmark agents use hidden observations, and add tests that other players cannot infer the inserted position through `information_state`.

- severity: major  
  evidence: Rulebook says `Wunsch` target chooses which card to give; code implements that. But `Pärchen` steals a random card and `Mischen` shuffles randomly; both are modeled through chance abstractions with card-title outcomes rather than physical card instances/permutations.  
  why it matters: Probabilities can be distorted when duplicate cards or deck permutations matter.  
  suggested next action: Decide whether title-level randomness is acceptable for BoardBench, or introduce card-instance identities.

- severity: minor  
  evidence: `Defuse` is used automatically when an Exploding Kitten is drawn. Rulebook says the player can play it instead of dying, and it is the only rescue described.  
  why it matters: This is probably harmless, but it removes an explicit decision point.  
  suggested next action: Keep as documented assumption or add an explicit `play:entschaerfung` response phase.

- severity: minor  
  evidence: Code allows `five:` to take one of the five just-played cards because they enter discard before resolution. Rulebook says five different cards may take any card from the discard pile.  
  why it matters: This is a plausible timing interpretation but may make five-card combos self-recover one played card.  
  suggested next action: Clarify whether “Ablagestapel” includes the just-played five cards for this effect.

### 3. Rule coverage review

| rule area | status | evidence | notes |
|---|---|---|---|
| setup | partially covered | Code sets aside Exploding Kittens/Defuses, deals 7 plus 1 Defuse, adds `n-1` kittens, handles 2-player Defuse variant | Deterministic deal and deck order replace shuffle/random setup |
| player count and turn order | covered correctly | Supports 2-5 players, clockwise next alive player, configurable start player | Start player is deterministic by default, acceptable as convention |
| legal actions | mostly covered | Pass, named cards, Favor, Nope, pair, triple, five-card combo | Does not allow playing inert single cat cards, which matches “alleine machtlos” |
| state transitions | partially covered | Implements drawing at end of turn, card effects, Nope resolution, attacks, skips, defuse insertion | Shuffle and random steal are simplified abstractions |
| terminal conditions | covered correctly | Terminal when one player alive; winner gets positive return | Matches “nur noch ein Spieler am Leben” |
| scoring/returns | covered correctly | Winner `1.0`, others `-1.0` | Rulebook only defines winner/losers, so numeric mapping is reasonable |
| rendering/action names | covered correctly | Stable render, canonical action names, round-trip helpers | Full render reveals hidden data, but `information_state` exists |
| chance | partially covered | Chance nodes for stealing and shuffle | No chance setup; shuffle outcome space is very small |
| hidden information | partially covered | Hands and deck stored fully; `information_state` hides other hands and deck order | Debug `render` is full-state and must not be used as player observation |
| simultaneous moves | unclear/not applicable | Rulebook has interruptible `Nö!`, not simultaneous move structure | Sequential response window is reasonable |

### 4. Unsupported Assumptions Or Invented Rules

- Harmless convention: deterministic start player `p0` unless configured, while rulebook lets players choose by any criterion.
- Risky abstraction: deterministic canonical setup instead of modeling the initial shuffle/deal as chance.
- Risky abstraction: `Mischen` has only a few artificial reorderings, not a real shuffle.
- Harmless/risky mixed: unnamed cat-card titles are replaced with one visible title and generic titles.
- Risky timing assumption: five-card combo can retrieve a just-played card from the discard pile.
- Mostly harmless assumption: Defuse is automatic when available.
- Risky simplification: random card stealing is by card title rather than individual physical card identity.
- Harmless convention: empty draw pile fallback simply ends the turn, despite the rulebook saying the pile should not run out.

### 5. Missing Scenario Tests

- Setup counts for 2, 3, 4, and 5 players: correct hands, draw pile counts, Exploding Kitten count, Defuse count.
- `pass` draws a safe card, adds it to hand, advances to next alive player.
- Drawing Exploding Kitten with no Defuse eliminates player and discards hand plus kitten.
- Drawing Exploding Kitten with Defuse enters insertion phase, then chosen position returns kitten and advances turn.
- `play:angriff` followed by all `decline_nope` gives next player two turns.
- `play:hops` during an attack consumes only one of two required turns.
- `play:noe` cancels an attack; second `play:noe` restores it.
- `play:wunsch->p1` enters give phase and lets target choose the card.
- `pair:<title>->p1` enters chance steal with probabilities matching target hand counts.
- `triple:<title>->p1:ask:<card>` transfers requested card only if present.
- `five:<five distinct titles>->discard:<card>` removes the selected discard card and adds it to actor hand.
- `information_state` after `Blick in die Zukunft` shows top cards only to the actor.

### 6. Open Questions For The Human

- Should BoardBench treat this as a deterministic reduced model, or should setup/shuffle be represented with fuller chance handling?
- Should `render()` be allowed to expose hidden state for debugging, or should benchmark comparison use only `information_state()` for this game?
- Should the five-card combo be allowed to retrieve one of the five cards just played?

```text
score: 0.70
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```