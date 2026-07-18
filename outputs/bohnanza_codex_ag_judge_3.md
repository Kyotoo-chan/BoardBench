## Assessment

`score: 0.78`, `confidence: high`

The module faithfully implements most setup, inventory, planting, trade transfer, harvest valuation, Ackerbohne, depletion, terminal scoring, and tie-break rules. Two material gaps remain: out-of-turn harvesting is unavailable to most players, and the consenting player cannot observe the proposed trade through the documented private-information view.

## Findings

### Major — Out-of-turn harvesting is restricted to the current decision player

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Evidence: `RULES`, PDF p.7, “Die Bohnenernte”: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Complete approved expectation: an owner may harvest between individual game steps, including during another player’s turn, but not inside an executing atomic draw or transfer.
- Conflicting symbols: `Game.legal_actions`, especially `p = state.decision`, `harvests = self._harvest_actions(state, p)`, and the equivalent phase-3 restriction.
- Expected: at every stable decision boundary, every player should be able to initiate a legal harvest of their own field, after which the pending phase decision resumes.
- Implemented: only `state.decision` receives harvest actions. During most of another player’s turn, non-decision players cannot harvest at all.

This affects tactical timing throughout planting, trading, and drawing and is therefore material.

### Major — A trade recipient cannot see the proposal they must accept or reject

- Canonical fact: `TRADE-05`
- Evidence type: `rule_quote`
- Evidence: `RULES`, PDF p.6, yellow “Beachte” section: “Denn beide Spieler müssen dem Handel zustimmen.”
- Complete approved expectation: the proposed cards stay in place until an atomic, informed acceptance; both participants explicitly consent to the specific transfer.
- Conflicting symbols/transitions:
  - `Game.apply_action`: `"Handel vorschlagen"` sets `awaiting_consent = True` and transfers `decision` to the partner.
  - `Game.legal_actions`: the partner then receives only `"Handel annehmen"` and `"Handel ablehnen"` choices.
  - `Game.render`: omits `state.trade`, including selected hand cards, revealed cards, requested cards, and partner.
- Expected: the recipient’s observation identifies the concrete offered and requested cards without exposing unrelated hidden hand information.
- Implemented: the recipient can accept or reject, but the rendered observation does not disclose what is being proposed. In particular, an offered card from the active player’s hidden hand cannot be inferred from `render()`.

The underlying transfer is consensual and atomic, but the information needed for meaningful consent is absent.

## Rule-area coverage

| Area | Status | Notes |
|---|---|---|
| Setup and inventory | Pass | 4–5 players, 129-card deck, five ordered cards, two initial fields |
| Turn order and phases | Pass | Four phases and clockwise progression |
| Phase-1 planting | Pass | Mandatory first, optional second, forced legal harvest |
| Reveal and trade | Partial | Transfers and consent work; proposal is not observable |
| Mandatory planting | Pass | All retained/received cards queued; recipient selects order |
| Harvest timing | Partial | Normal harvest mechanics pass; out-of-turn access is missing |
| Harvest yields | Pass | All ordinary thresholds and special Garden yield match |
| Ackerbohne | Pass | One, two, and three-card outcomes match approved decisions |
| Draw and depletion | Pass | Reshuffle and third-depletion phase boundaries match |
| Private information | Partial | Hands are hidden appropriately, but trade details are over-hidden |
| End, winner, returns | Pass | Final harvest, hand exclusion, tie-break, and winner returns match |
| Elimination | Pass | None implemented |

## Missing deterministic scenarios

The permitted implementation artifact does not supply deterministic scenarios. The most important additions are:

1. A non-active, non-decision player harvests between two ordinary actions, and the original pending decision resumes unchanged.
2. A trade mixing hidden-hand and revealed cards is proposed; the recipient observes exactly the proposal, then accepts or rejects it.
3. Singleton protection with both an existing multi-card field and only singleton fields.
4. Ackerbohne harvests of one, two without field 3, two with field 3, and three.
5. First/second depletion during a two-card reveal, including continuation from the reshuffled discard.
6. Third depletion during phase 2 versus phase 4, verifying their distinct terminal boundaries.
7. Final tied coin totals, verifying the farthest-clockwise-from-start-player winner.

## Material questions for a human

- Is player index `0` intentionally a canonical relabeling of the chosen start player? If so, fixed `active = 0` is sufficient; otherwise the constructor needs a start-player parameter.
- Is `render()` the authoritative player observation, or is public action history supplied separately? Public history could help reconstruct parts of a trade, but hidden-hand offers still need a safe card-identity representation.
- Must transitions be reproducible when branching twice from the same `GameState`? The random generator lives on `Game`, not in the state, so identical reshuffle transitions can differ depending on prior branch execution. The supplied rules do not decide this interface issue.

score: 0.78
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
