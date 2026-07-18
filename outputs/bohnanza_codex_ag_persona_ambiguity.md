## Review outcome

One material ambiguity remains unresolved: the order in which different players complete phase-3 planting. Harvest timing, start-player designation, singleton Ackerbohne harvesting, and conflicting Ackerbohne text have approved human resolutions. The implementation does not fully honor the approved harvest-timing or start-player decisions.

## Ambiguous rules

### 1. Meaning of “harvest at any time”

- **Source:** RULES, PDF p.7: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
  **Fact:** HARV-01.
- **Plausible interpretations:**
  1. Any player may interrupt virtually any operation to harvest.
  2. Any player may harvest only at stable boundaries between indivisible actions such as a draw, transfer, or planting.
- **Implementation choice:** Harvest actions are offered only to `state.decision`, not every player: [implementation.py:104](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_ambiguity_yk5169l6/implementation.py:104), especially lines 107–108. During trade consent, only the responding partner can harvest (lines 124–125); during phase 4, only the current drawer can harvest (lines 148–149).
- **Affected behavior:** Legal harvest actions during other players’ decisions; field contents; coins; Ackerbohne third-field acquisition; discard composition before reshuffles; potentially later draws and the winner.
- **Approved decision:** Yes. HARV-01 resolves this as harvesting by any owner between individual game steps, including during another player’s turn, but never inside an executing atomic draw or transfer. The temporal-boundary decisions reinforce that interpretation.
- **Assessment:** The source ambiguity is resolved, but the implementation adopts a narrower, decision-player-only behavior inconsistent with that resolution.
- **Clarification:** “After every completed atomic action and before the next action begins, every player may choose to harvest one of their own legally harvestable fields.”

### 2. Order among different players in phase 3

- **Source:** RULES, PDF p.7: “Alle Spieler, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen.” and “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Karten anbaut.”
  **Facts:** P3-01, P3-02.
- **Plausible interpretations:**
  1. Players resolve in a fixed order—such as active player first, then clockwise—while each player chooses the order of their own cards.
  2. Eligible players may act in any order or interleave individual plantings, with each card owner selecting when to plant.
- **Implementation choice:** The queue is grouped by numeric player index, and the lowest-numbered owner is selected first and continues until no cards belonging to that lower-numbered owner remain: [implementation.py:240](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_ambiguity_yk5169l6/implementation.py:240), particularly lines 241–249. This is not necessarily clockwise from the active player.
- **Affected behavior:** Who sees whose planting or harvesting decisions before acting; when forced harvests occur; legal action order; discard contents and strategic choices; consequently coin totals and terminal results.
- **Approved decision:** No. P3-02 establishes each recipient’s control over the order of their own cards, but neither it nor the temporal-boundary section selects an order among recipients.
- **Assessment:** This is the principal unresolved material source ambiguity. The implementation makes a defensible but unsupported numeric-seat assumption.
- **Clarification:** “Beginning with the active player and proceeding clockwise, each player with sideways cards plants all of their cards, in an order of their choice, before the next player begins.”

## Missing rules

### 3. How the start player is selected or supplied

- **Source:** RULES, PDF p.2: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
  **Fact:** SET-03.
- **Plausible interpretations:**
  1. Players choose the start player socially, and the engine must accept that player as setup input.
  2. The game randomly selects the start player.
- **Implementation choice:** Player 0 is always active and the decision player initially (lines 46–48), and the constructor exposes no start-player parameter: [implementation.py:64](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_ambiguity_yk5169l6/implementation.py:64). The tie-break explicitly assumes player 0 was the start player (lines 197–198).
- **Affected behavior:** First turn, all clockwise turn positions, phase-4 draw order, and the tie-break winner.
- **Approved decision:** Yes. SET-03 requires one configured/chosen start player who keeps the marker. It does not authorize fixing that role permanently to player 0 unless seat numbering is explicitly normalized around the prior choice.
- **Assessment:** The rulebook leaves the selection procedure open, but the approved model resolves this through configuration. The implementation silently normalizes it to seat 0 without documenting that normalization.
- **Clarification:** “Before dealing, choose a start player; in a digital implementation, that player’s seat index must be supplied during setup.”

### 4. Harvesting a single Ackerbohne

- **Source gap:** RULES, PDF p.11 explains the results for two and three Ackerbohnen but gives no explicit result for one: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld” and “Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.”
  COMPONENTS, PDF p.2: “1 Ackerbohne — 0 Taler — Normale Null-Ernte.”
  **Fact:** ACKER-04.
- **Plausible interpretations:**
  1. One Ackerbohne may be harvested normally for zero coins, subject to the protection rule.
  2. The special Ackerbohne schedule permits harvesting only at two or three cards.
- **Implementation choice:** A single Ackerbohne earns zero, its card is discarded, and the field empties: [implementation.py:163](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_ambiguity_yk5169l6/implementation.py:163), lines 172–180. General harvest protection still applies at lines 89–93.
- **Affected behavior:** Whether a player can clear an Ackerbohne field; forced planting options; access to empty fields; discard contents.
- **Approved decision:** Yes. ACKER-04 explicitly approves the ordinary zero-yield harvest.
- **Clarification:** “A field containing exactly one Ackerbohne may be harvested for zero coins whenever the normal bean-protection rule permits it.”

## Contradictory rules

### 5. Two-Ackerbohne reward

- **Conflict recorded in approved facts:** The correction section identifies COMPONENTS p.3 wording “2 Karten = 2 [Taler]” as a transcription error.
- **Controlling source:** RULES, PDF p.11: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
  **Facts:** ACKER-01, ACKER-02.
- **Plausible interpretations absent the correction:**
  1. Two Ackerbohnen award two coins.
  2. Two Ackerbohnen unlock the third field and award no coins.
- **Implementation choice:** Two cards unlock a third field if absent, then both are discarded; if it already exists, they are simply discarded: [implementation.py:166](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_ambiguity_yk5169l6/implementation.py:166).
- **Affected behavior:** Coin totals, permanent field capacity, future planting legality, and terminal winner.
- **Approved decision:** Yes. The publisher rule controls; two never award two coins. The implementation follows the approved resolution.
- **Clarification:** “Harvesting exactly two Ackerbohnen awards no coins; it unlocks field 3 only if that field is not already available.”

The approved correction also declares conflicting COMPONENTS Saubohne prose a transcription error. RULES p.8 controls under GOLD-03: 3–4 cards yield 1 coin, 5–6 yield 2, 7 yields 3, and 8+ yields 4. The implementation uses those thresholds at [implementation.py:18](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_persona_ambiguity_yk5169l6/implementation.py:18).

## Merely untestable or intentionally unscored

These are expressly left unresolved and should not be converted into implementation findings:

- Social negotiation wording, voluntary hand disclosure, conditional promises, and multi-party arrangements.
- Timing inside an already executing atomic action.
- Exact counts of non-bean mats and overview cards beyond one per participant.
- Artificial states where both deck and discard contain too few cards for a nonterminal owed draw.

## Material-assumption summary

- **Unresolved implementation assumption:** Phase-3 recipients act in ascending numeric seat order and cannot interleave. The canonical material does not select this order.
- **Resolved but not fully implemented:** Any player may harvest between atomic actions; the code generally restricts harvesting to the current decision player.
- **Resolved but silently normalized:** The selected start player is always represented as player 0; this normalization is neither configurable nor documented.
- **Resolved and implemented:** Singleton Ackerbohne harvests yield zero; two unlock field 3 without coins; three yield three coins.
- **No Judge score was emitted or modified.**
