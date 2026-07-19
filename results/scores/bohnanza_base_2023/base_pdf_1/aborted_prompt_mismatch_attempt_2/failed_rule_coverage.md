# Rule coverage audit

Evidence is the supplied publisher rulebook (`game_rules.pdf`, pages 1–2, including the
fresh page images). The implementation is scoped to the assigned 4–5-player condition.

| Supplied section / named rule | Implementation coverage |
|---|---|
| Spielidee | Bean fields, trading, harvesting, coin scoring, and most-coins victory are modeled. |
| Spielmaterial & Spielvorbereitung | All 104 cards are represented: Gartenbohne 6, Rote Bohne 8, Augenbohne 10, Sojabohne 12, Brechbohne 14, Saubohne 16, Feuerbohne 18, Blaue Bohne 20. Four/five players receive two fields and five cards. Start player is retained. Deck is shuffled from the seed. |
| Wichtigste Regel des Spiels (hand order) | Hands are ordered lists. The first card must be planted; draws append without reordering. Trade references may select any hand position, and accepted cards never enter a hand. |
| Spielablauf | Active player and clockwise succession are explicit; all four phases and intermediate consent/planting phases are represented. |
| Wichtige Regeln für den Bohnenanbau | Fields contain one bean type; the same type may occupy multiple fields. Only compatible or empty fields are legal plant targets. A harvest is required before an otherwise impossible mandatory plant. |
| 1. Phase: Bohnenkarten von der Hand anbauen | First front card is mandatory, second front card optional, never a third; empty-hand start skips by `pass`. |
| 2. Phase: Bohnenkarten aufdecken und handeln | Up to two top deck cards are revealed and owned by the active player for planting/trading. Active player alone proposes with every player. Any hand location and active revealed cards are valid references; field and received cards are excluded. Unequal multi-card bundles are accepted by the transition validator. Both parties consent. Accepted cards go to `pending_received`, not hands, and cannot be retraded. Gifts require recipient consent. Trading can continue after revealed cards trade; active player explicitly ends it. |
| Regeln für den Bohnenhandel | Active-only dealing, no third-party deals, arbitrary hand positions, active revealed cards, no received/field-card trading, unequal quantities, mutual assent, and gift refusal are covered. Canonical legal-action enumeration provides each single-card exchange/gift; `apply_action` additionally supports every valid unequal bundle without changing the finite normal action surface. |
| 3. Phase: Gehandelte und aufgedeckte Bohnenkarten anbauen | Every received and untraded revealed card must be planted. Each player controls their order; incompatible cards require a prior legal harvest. |
| 4. Phase: Bohnenkarten nachziehen | Active player draws up to three sequential cards and appends them in order, then active play passes clockwise. |
| Die Bohnenernte | Every player can harvest at any time, including off-turn. Each named bean's printed Bohnometer is encoded: Garten 2/3; Rot 3/4/5/6; Auge 2/4/5/6; Soja 2/4/6/7; Brech 3/5/6/7; Sau 3/5/7/8; Feuer 3/6/8/9; Blau 4/6/8/10 (thresholds for 1–4 coins; absent Garten tiers omitted). Paid cards become the integer coin total, remainders go to discard, and the field empties. Zero-coin harvests work. |
| Die Bohnenschutzregel | A singleton field cannot be harvested while that same player has any field with more than one card. |
| Ein leerer Nachziehstapel | Drawing the last card increments depletion; after the first and second depletion the discard is deterministically shuffled into the new deck. |
| Ende des Spiels | Third deck depletion ends immediately except that depletion while phase-2 revealing completes trading and mandatory phase-3 planting. All fields are finally harvested, hands do not score, each coin is one point, highest total wins, and a scoring tie goes to the tied player farthest clockwise from the retained start player. |
| Beispiele 1–5 | The illustrated reveal/offer, enlarged unequal offer, accepted cards beside fields, mandatory planting by both parties, and 3-Feuerbohne one-coin harvest are all representable. |
| Canonical environment/profile | Strict state/action envelopes, complete privileged state, hidden opponent hands in observations, detached JSON payloads, deterministic seeded chance, reconstruction of complete fixture states (including reserve and unusual phases), and human/canonical action round trips are implemented. |
