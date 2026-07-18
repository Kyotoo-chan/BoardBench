## 1. Score

**Score: 0.18 — confidence: high.**

The module cannot initialize the assigned 129-card Ackerbohne condition. Its base-game fallback models several mechanics reasonably well, but independently contradicts the selected variant’s draw phase, mandatory planting-order choice, private-hand convention, and depletion timing. Final harvesting and winner/tiebreak calculation are largely sound once terminal scoring is reached.

## 2. Findings

### Critical

1. **The assigned Ackerbohne game cannot start**

   - Canonical facts: `INV-03`, `INV-04`, `ACKER-01`
   - Evidence types: `rule_quote`, `user_observation`
   - Sources:
     - `RULES`, PDF p.10: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen.”
     - `COMPONENTS`, `/bohnen/9/anzahl_karten`: Weinbrandbohne `22`.
     - `COMPONENTS`, `/bohnen/11/anzahl_karten`: Ackerbohne `3`.
     - `RULES`, PDF p.11: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
   - Conflicting symbols: `Game.initial_state`, `BASE_COUNTS`, `METERS`, `_harvest`
   - Expected: The selected four/five-player game constructs a 129-card deck containing the eight base types, 22 Weinbrandbohnen, and three Ackerbohnen, with the special Acker harvest/third-field behavior.
   - Implemented: `initial_state()` raises `ValueError` for `variant="Ackerbohnen"`. Only the 104-card base deck is constructible; Weinbrandbohne is absent and Ackerbohne’s special harvest behavior is not implemented.
   - Impact: No legal playthrough of the assigned source condition is possible.

### Major

2. **Phase 4 uses the base-game three-card draw instead of the selected variant draw**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.10: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting transition: `apply_action(..., ("draw_phase4",))`
   - Expected: Every player draws one card, active player first and then clockwise; each card appends to its recipient’s hand.
   - Implemented: `for _ in range(3)` draws three cards, all appended to `s.hands[s.active]`. No other player draws.
   - Impact: Materially changes hand sizes, card distribution, deck depletion, and future turns.

3. **Mandatory phase-3 planting order is fixed rather than chosen by each recipient**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.7: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting symbols: `end_trade`, `s.pending`, phase-3 `plant`
   - Expected: Each player chooses the order in which their received/revealed cards are planted, including where that order affects intervening harvest choices.
   - Implemented: `end_trade` creates one fixed `pending` sequence by player index and receipt order. Phase 3 permits planting only `s.pending[0]`.
   - Impact: Removes a material strategic choice and can force different harvests or field outcomes.

4. **The only rendered state exposes every ordered hand to every observer**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p.3; approved decision: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
   - Conflicting symbol: `Game.render`
   - Expected: A player-specific observation contains that player’s ordered hand, but only hand counts for opponents.
   - Implemented: `render()` serializes the complete `hands` array without an observing-player parameter or redaction.
   - Impact: Unless `render` is explicitly restricted to an omniscient administrative channel, it leaks private information and materially affects trading.

5. **Pile depletion is recognized on the next attempted draw, not when the last card is drawn**

   - Canonical facts: `DECK-01`, `END-01`, `END-05`
   - Evidence types: `rule_quote`, `human_decision`
   - Sources:
     - `RULES`, PDF p.9: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
     - `RULES`, PDF p.9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - Approved `END-05` decision: “If third depletion occurs during variant phase 4, stop immediately after the draw that empties it; no remaining players draw.”
   - Conflicting symbol: `_draw_one`
   - Expected: Popping the last card immediately records depletion. On the first two occurrences, the then-current discard pile is shuffled immediately; on the third phase-4 occurrence, the game ends after that draw.
   - Implemented: `s.exhaustions` increments only when `_draw_one` begins with an already-empty deck. If a draw pops the last card, play continues until another draw is attempted.
   - Impact: The game can continue into later actions or turns after its terminal trigger. Delayed reshuffling can also include cards discarded after the actual depletion, changing chance outcomes.
   - Provenance note: The immediate phase-4 stopping boundary is an approved human adjudication; it is separate from the printed third-depletion rule itself.

### Minor

6. **The 14-card bean type has an unsupported identity**

   - Canonical facts: `INV-02`, `GOLD-04`
   - Source: `COMPONENTS`, `/bohnen/3/name`: `Brechbohne`; `/bohnen/3/anzahl_karten`: `14`.
   - Conflicting symbols: `BASE_COUNTS`, `METERS`
   - Expected: The 14-card type is Brechbohne.
   - Implemented: It is named `Grüne Bohne`, although it uses Brechbohne’s count and meter.
   - Impact: The arithmetic is correct, but actions and rendered state expose a card identity absent from the canonical inventory.

## 3. Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Selected setup/inventory | Failed | Acker condition rejected; 129-card deck unavailable |
| Initial deal/hand order | Partial | Five-card ordered deal and append behavior are correct |
| Private information | Failed | Full hands rendered globally |
| Turn order/phases 1–2 | Mostly covered | Clockwise active player and mandatory/optional hand planting are represented |
| Trading | Mostly covered | Active-player-only, consensual, unequal exchanges and gifts are represented |
| Phase-3 planting | Failed | All cards are pending, but their order cannot be chosen |
| Variant phase-4 draw | Failed | Three cards go to active player |
| Normal harvesting/meters | Mostly covered | Base thresholds and singleton protection are substantially correct |
| Acker harvesting/third field | Absent | Special rewards and field unlock unavailable |
| Depletion/reshuffle | Failed | Trigger is one attempted draw late |
| Terminal scoring/tiebreak | Covered | Fields harvest, hands do not score, farthest clockwise tied seat wins |
| Returns/elimination | Covered | Nonterminal zero; winner indicator terminal; no elimination |

## 4. Missing deterministic scenarios

- Construct four- and five-player Acker games; verify 129 cards before dealing and correct remaining-deck sizes afterward.
- Verify all ten selected bean identities and counts.
- Harvest one, two, and three Ackerbohnen, including two with an already unlocked third field.
- Verify phase 4 gives exactly one appended card to every player in clockwise order.
- Give a player multiple pending beans whose two planting orders produce different legal harvest consequences.
- Exhaust the pile exactly on the first or second revealed card and verify immediate depletion handling.
- Exhaust it on the last phase-4 draw and verify immediate terminal state with no later action or draw.
- Verify cards discarded after depletion are not retroactively included in the already-required reshuffle.
- Compare observations for the hand owner and an opponent.
- Verify the canonical Brechbohne identity through setup, legal actions, and rendering.

## 5. Material questions for a human

- Is `render()` intended as a privileged omniscient debugging representation, or as the player-facing observation? If privileged, a separate player-specific observation API is still absent.
- Is seat zero intentionally the externally chosen start player? The implementation fixes `start_player = 0` and offers no configuration, though this can be acceptable if seat assignment itself performs the choice.

Neither question reflects ambiguity in the supplied gameplay rules, so no rulebook clarification is required.

```text
score: 0.18
confidence: high
critical_issues: 1
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```