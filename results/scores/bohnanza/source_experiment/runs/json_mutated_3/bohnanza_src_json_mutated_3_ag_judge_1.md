score: 0.30  
confidence: high

The module captures several base mechanics—ordered hands, the first/optional-second planting sequence, protection-based harvesting, ordinary Bohnometers, consensual trades, and tie-breaking—but implements the wrong deck/variant, the wrong phase-4 draw, and incorrect depletion timing. These defects materially change card flow, scoring, and game termination.

## Findings

### Critical

1. **Deck depletion is detected one draw too late**

   - Canonical fact: `END-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 9
   - Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
   - Conflicting code: `Game._draw_one`
   - Expected: Drawing the last card causes a depletion immediately. On the third depletion, the applicable phase-2 or phase-4 ending boundary begins at that moment.
   - Implemented: `empty_count` increases only when a later draw starts with an already-empty deck. Popping the final card does not register depletion. Consequently, a pile emptied by the second reveal can be treated as depleting during phase 4, while a phase-4 draw that takes the final card may allow another turn. This can change the final planting opportunities, harvested fields, and winner.

### Major — contradictions of printed rules or user-observed components

2. **The selected 129-card Ackerbohne deck is replaced by the 104-card base deck**

   - Canonical facts: `INV-03`, `INV-04`
   - Evidence types: `rule_quote`, `user_observation`
   - Sources:
     - `RULES`, PDF page 10: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen”
     - `COMPONENTS`, JSON Pointers `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`: Weinbrandbohne `22`; Ackerbohne `3`
   - Conflicting code: `BEANS`, `METER`, `Game.initial_state`
   - Expected: Eight base types plus 22 Weinbrandbohnen and 3 Ackerbohnen, totaling 129 cards.
   - Implemented: `BEANS` contains only the eight base types and constructs exactly 104 cards. Both selected-variant types are absent, materially changing probabilities and game length.

3. **Ackerbohne fields, third-field unlocking, and special rewards are absent**

   - Canonical facts: `ACKER-01`, `ACKER-03`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 11
   - Exact evidence:
     - “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
     - “Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.”
   - Conflicting code: `GameState.fields`, `Game.initial_state`, `_harvest_actions`, `_can_plant`, `_do_harvest`
   - Expected: Two Ackerbohnen can unlock a persistent third field; three yield three coins. The approved one-card and already-unlocked cases must also be supported.
   - Implemented: Every player permanently has exactly two fields, all field loops use `range(2)`, and Ackerbohne has no meter or harvesting path.

4. **Phase 4 uses the base-game “active player draws three” rule**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Exact evidence: “zieht jeder von euch eine Karte vom Nachziehstapel … der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting code: phase `"draw_three"` and `apply_action` branch `kind == "draw_three"`
   - Expected: Each player draws one card, beginning with the active player and proceeding clockwise.
   - Implemented: Only the active player draws three cards. This changes every hand and which player causes third depletion.

5. **Trades cannot exchange unequal or multi-card quantities**

   - Canonical fact: `TRADE-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 5
   - Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
   - Conflicting code: `proposal`, `propose_trade`, `_accept`
   - Expected: A consensual trade may transfer multiple cards and unequal quantities.
   - Implemented: A proposal contains one `give` and at most one `receive`, restricting exchanges to one-for-one or a single outgoing gift.

6. **Gifts are only supported from the active player to another player**

   - Canonical facts: `TRADE-01`, `TRADE-07`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF pages 5–6
   - Exact evidence:
     - “Nur du als aktiver Spieler darfst mit anderen Spielern handeln.”
     - “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
   - Conflicting code: trade-phase `legal_actions`, `propose_gift`, `_accept`
   - Expected: A gift involving the active player is legal with recipient consent, including an inactive player giving to the active player.
   - Implemented: Only the active actor can propose a gift, and `give` must come from the active player’s hand or reveals.

### Major — deviations from approved human decisions

7. **Non-acting owners cannot harvest between game steps**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Approved boundary: Owners may harvest between individual game steps, including during another player’s turn, but not inside an atomic draw or transfer.
   - Conflicting code: `_harvest_actions` and `legal_actions`
   - Expected: Eligible non-active owners must receive explicit harvest opportunities at approved step boundaries.
   - Implemented: Harvest actions exist only for `state.actor`. During most phases this is the active player; during a proposal it is solely the recipient.

8. **Legal trade actions reveal opponents’ private bean types**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Exact source evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
   - Approved decision: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
   - Conflicting code: trade branch of `legal_actions`, especially `for receive in dict.fromkeys(state.hands[target])`
   - Expected: An active player’s observation exposes only opponents’ hand counts unless information is voluntarily communicated.
   - Implemented: The available `propose_trade` actions enumerate every distinct bean type in each opponent’s hand, disclosing private contents.

### Minor

9. **A hand card and revealed card of the same type cannot be distinguished in a trade**

   `legal_actions` collapses `state.hands[p] + state.revealed` by bean name, while `_remove_active_card` always removes a matching revealed card first. Thus the legal choice to trade a hand copy while retaining the identical reveal is unavailable. This conflicts locally with `TRADE-02`, which permits trading any hand position and also permits trading revealed cards.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count/setup | Partial | Supports 4–5 and five-card ordered hands; selected deck and third-field system absent |
| Hand planting | Mostly covered | Mandatory first, optional second, no third |
| Reveal | Partial | Reveals two, but depletion boundary is wrong |
| Trading/gifts | Material gaps | Consent and active-player participation exist; multi-card trades, inbound gifts, and privacy fail |
| Mandatory planting | Mostly covered | Acquired and retained reveals are planted with selectable order |
| Phase-4 draw | Contradicted | Active draws three instead of everyone drawing one |
| Ordinary harvesting | Mostly covered | Standard meters and protection work; timing access is incomplete |
| Acker harvesting | Absent | No Ackerbohne or third field |
| Reshuffle/depletion | Incorrect | Depletion is registered on the next attempted draw |
| End scoring | Partial | Ordinary final harvest and tie-break exist; Acker scoring and correct end timing do not |
| Returns/observability | Partial | Nonterminal zero and terminal winner returns exist; trade actions leak private information |

## Missing deterministic scenarios

- Last card taken by the first or second phase-2 reveal on each depletion count.
- Third depletion caused by a phase-4 draw, verifying immediate termination before the next player draws.
- Phase 4 with four and five players, verifying one clockwise draw per player.
- Exact 129-card inventory and deterministic initial deal from that inventory.
- Harvesting two Ackerbohnen with and without an existing third field.
- Harvesting one and three Ackerbohnen.
- Planting into an unlocked third field on later turns.
- Unequal trades such as two cards for one and one for two.
- Inactive-player gift to the active player with acceptance and rejection.
- Same-type hand/reveal trade-source selection.
- Non-active owner harvest opportunities between planting and trade steps.
- Observation test ensuring opponent bean identities cannot be inferred from legal actions.
- Phase-2 third depletion followed by completion of trading and all mandatory planting, with phase 4 skipped.

## Material questions for a human

- Should pending received cards be included explicitly in `render()` for all players? The physical placement beside fields suggests public information, but the approved facts do not expressly define their observation encoding.
- Should the action protocol model voluntarily communicated requested bean types, or use opaque/indexed opponent responses so legal-action enumeration cannot disclose hidden hands?

score: 0.30
confidence: high
critical_issues: 1
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true