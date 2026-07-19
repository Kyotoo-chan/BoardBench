# Rule coverage audit

Source authority: `game_rules.pdf` (publisher rulebook), including both supplied page images. The packet contains no user-observation component source.

| Supplied section / named rule | Implementation coverage |
|---|---|
| Spielidee | Fields, trading, harvesting, coin scoring, and most-coins victory are modeled. |
| Spielmaterial & Spielvorbereitung | 104-card inventory; counts 6/8/10/12/14/16/18/20; all eight named beans; five ordered starting hand cards; fixed start player; 4–5 players use two fields. |
| Hand-order rule | Hands are lists; the first card is mandatory; deals/draws append without reordering; trades may reference any hand position. |
| Spielablauf | Fixed active/start player data, clockwise turns, and all four phases are modeled. |
| Wichtige Regeln für den Bohnenanbau | A field is empty or contains one bean kind; the same kind may occupy multiple fields; cards append to field rows. |
| 1. Phase: Bohnenkarten von der Hand anbauen | First card mandatory, second card optional, never a third; empty hand skips; a required incompatible bean necessitates a legal harvest before planting. |
| 2. Phase: Bohnenkarten aufdecken und handeln | Up to two top cards reveal publicly; they belong to the active player until planted/traded. |
| Regeln für den Bohnenhandel | Only active player proposes with each other player; any hand positions and active revealed cards; field/received cards excluded; unequal offers through the evidenced two-for-one size; proposals require consent; rejection changes nothing; received cards stage beside fields and cannot enter hand or be retraded. |
| Geschenkregel | One-way proposals in either direction are marked gifts and require recipient/partner consent. |
| 3. Phase: Gehandelte und aufgedeckte Bohnenkarten anbauen | Every staged card and untraded reveal must be planted; each affected player chooses order; harvesting can make room. |
| 4. Phase: Bohnenkarten nachziehen | Active player draws sequentially up to three, appends in order, then active player advances clockwise. |
| Die Bohnenernte | Harvest is available at any time, including off-turn; printed bean meters determine coins; coin cards are removed from the field and remaining cards go to discard; field becomes empty. |
| Printed Bohnometers | Gartenbohne 2→2, 3→3; Rote Bohne 2/3/4/5→1/2/3/4; Augenbohne 2/4/5/6; Sojabohne 2/4/6/7; Brechbohne 3/5/6/7; Saubohne 3/5/7/8; Feuerbohne 3/6/8/9; Blaue Bohne 4/6/8/10 (the latter seven maps yield 1/2/3/4 coins). |
| Die Bohnenschutzregel | A singleton field cannot be harvested while any own field has more than one card. |
| Ein leerer Nachziehstapel | Taking the last deck card increments depletion; before the third depletion, discard is deterministically shuffled into a new deck. |
| Ende des Spiels | Third depletion ends immediately except that depletion during reveal completes phases 2 and 3; all fields are then harvested, hands ignored, coins scored; tie goes farthest clockwise from fixed start player. |
| Named examples 1–5 | Reveal/retain/trade request; expanded multi-card offer; received-card staging; participant-chosen planting; and meter-based Feuerbohne harvest are all representable. |
| Canonical environment contract/profile | Strict detached state/action envelopes, fixture reconstruction, hidden opponent hands in observations, stable actions, seed/chance state, reserve zone, pending consent, and 4/5-player configurations are implemented. |

All profile bean IDs are audited: `gartenbohne`, `rote_bohne`, `augenbohne`, `sojabohne`, `brechbohne`, `saubohne`, `feuerbohne`, `blaue_bohne`.
