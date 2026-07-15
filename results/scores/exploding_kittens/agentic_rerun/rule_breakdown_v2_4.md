# Exact rule breakdown under `expl-v2.4`

This report distinguishes the canonical expectation, its evidence basis, the r2 implementation behavior, and the likely origin of each mismatch. `clear` means directly scored from printed wording; `human_decision` means an approved adjudication of an ambiguity or executable boundary.

## Canonical executable expectations

| ID | Basis | Defined expectation | Canonical quote (page) |
|---|---|---|---|
| R01 | clear | A two-player game starts nonterminal at player 0 with at least one legal action and zero returns. | “Zusätzlich erhält jeder Spieler eine Karte ‚Entschärfung‘. So starten alle mit 8 Karten auf der Hand.” (p.1) |
| R02 | clear | A normal turn exposes a draw/pass action that can end the turn. | “Du beendest deinen Zug, indem du die oberste Karte vom Spielstapel ziehst.” (p.1) |
| R03 | clear | Attack ends the actor’s turn without drawing and gives the next player exactly two owed turns. | “... zwingst den nächsten Spieler, zwei Spielzüge direkt nacheinander auszuführen.” (p.2) |
| R04 | clear | With two owed turns, one Skip leaves the same player owing one turn; a second Skip passes play onward with normal debt 1. | “... überspringst du nur einen der zwei Züge. Du müsstest schon zweimal ‚Hops!‘ ausspielen ...” (p.2) |
| R05 | clear | Preview reveals information but keeps the current player and current owed turn. | “Nachdem du die Anweisung der Karte befolgt hast, kannst du weitere Karten spielen ...” (p.1) |
| R06 | clear | Shuffle keeps the current player and current owed turn. | same turn-continuation quote (p.1) |
| R07 | clear | Favor transfers one donor-chosen card and returns control to the actor without ending the turn. | “Dieser Spieler entscheidet, welche Karte du bekommst.” (p.2) |
| R08 | clear | Drawing a Kitten without Defuse eliminates the player; the sole survivor wins and no actions remain. | “Der Spieler, der nicht explodiert und als Letzter übrig ist, gewinnt.” (p.1) |
| R09 | human_decision | A chained Attack **replaces** all remaining debt with exactly two turns for the next player; it does not add debt. | “... ist er nicht mehr an der Reihe und der nächste Spieler muss zwei Spielzüge ausführen.” (p.2) |
| R10 | human_decision | Defuse is mandatory when held: after drawing a Kitten, no voluntary explode/decline action is legal. | Source says “kannst ... statt zu sterben” (p.2); mandatory use is the approved adjudication. |
| R11 | human_decision | Defusing consumes exactly the current owed turn. With debt 2, the same player remains active with debt 1. | “Dann ist dein Spielzug beendet.” (p.2) |
| R12 | clear | The five different components are discarded before retrieval, so one of those five newly discarded cards may immediately be retrieved: final hand size 1, discard size 4. | “... 5 verschiedene Karten ... beliebige Karte aus dem Ablagestapel ...” (p.2) |
| R13 | human_decision | Retrieving a Kitten from discard is safe because it is not drawn from the deck. The player remains alive and holds the Kitten. | Five-card quote (p.2); safe retrieval is the approved draw-versus-take adjudication. |
| R14 | human_decision | An empty-handed player is not a legal Favor target because that player cannot give a card. | “Zwinge ... dir eine Karte zu geben.” (p.2) |
| R15 | human_decision | An empty-handed player is not a legal pair target because no random card can be stolen. | “... um einem Mitspieler eine zufällige Karte zu stehlen.” (p.2) |
| R16 | human_decision | A triple may request a Kitten if the target holds one; “a card” is not restricted to ordinary cards. | “... dass du dir eine Karte ... wünschen darfst.” (p.2) |
| R17 | clear | A same-title Cat pair action is not only named but executable and transfers one random card while keeping the actor’s turn. | “ALLE gleichen Karten als Pärchen ... eine zufällige Karte ... stehlen.” (p.2) |

## r2 failure matrix

`✓` means the deterministic scenario passes. Only failed IDs are listed.

| r2 condition | Clear failures | Human-decision failures |
|---|---|---|
| Original PDF | R12 | R10 |
| Faithful TXT | R12 | R10, R14, R15 |
| Anonymized | — | R14, R15 |
| Omissions | R12 | R10, R13, R14, R15, R16 |
| False rules | R04, R12 | R10, R13, R14, R15 |
| Vague rules | R12 | R09, R13, R14, R15, R16 |

All other scenarios pass. There are no crashes, unreached cases, or untestable cases.

## How each r2 generator interpreted the rules

### Original PDF r2

- **R10:** The implementation treats “kannst” literally as optional. After drawing a Kitten with Defuse, it exposes both a Defuse action and `Exploding Kitten:explodieren`. This conflicts with our mandatory-use adjudication, not with an unambiguous imperative in the source.
- **R12:** It implements a five-card effect, but creates that action only when a retrievable card already exists in discard. With an initially empty discard, it never exposes the combination, so it cannot retrieve one of its own five components. This is an implementation-order defect.
- **Correctly handled:** Attack debt, chained Attack replacement, two Skips, safe Kitten retrieval, empty targets, Kitten request by triple, and executable Cat pair.

### Faithful TXT r2

- **R10:** Like PDF r2, it offers `explode` even when Defuse is held. The model interpreted “kannst” as a real choice.
- **R12:** Five-card actions are enumerated from cards already present in discard. The five components are not considered retrievable when the action is selected, so no action exists for an initially empty discard.
- **R14/R15:** It enumerates Favor and pair actions for every living opponent, even when the target hand is empty. Resolution merely does nothing on an empty hand. Our adjudication requires such targets to be illegal up front.
- **Correctly handled:** Attack gives two turns and chained Attack replaces debt with two. Earlier v2.2 results incorrectly showed these as failures because the evaluator mistook the next player’s normal `Passen:draw` for a reaction pass.

### Anonymized r2

- The model mapped the replacement vocabulary coherently: `Gefahrenkarte`→Kitten, `Schutzkarte`→Defuse, `Doppelzug`→Attack, `Überspringen`→Skip, and so on.
- **R14/R15:** Its only deterministic mismatches are empty targets. It exposes `play:Auswahl->player:1` and `pärchen:...->player:1` for an empty target, then resolves them as no-ops.
- **Correctly handled:** It makes Schutzkarte mandatory, consumes one owed turn, permits a five-card component to be retrieved, treats retrieved Gefahrenkarte as safe, and lets a triple request Gefahrenkarte.
- Evaluator versions v2.2 and v2.3 initially undercounted this implementation because semantic action matching did not yet recognize its declared anonymized labels. That evaluator error is not attributed to the generator in v2.4.

### Omissions r2

- The module explicitly documents: **“Fünfling is not modelled.”** Therefore R12 and R13 fail directly because the supplied variant removed the five-card rule and the generator refused to invent it. These are source-omission-induced absences under canonical evaluation.
- **R10:** Remaining overview text led it to expose both Defuse and explode; it treats Defuse as optional.
- **R14/R15:** Favor and pair are legal against every living opponent regardless of hand size; empty resolution becomes a no-op.
- **R16:** Triple request choices exclude Exploding Kitten. The omitted source did not remove the triple wording, so this is an implementation assumption rather than a direct consequence of the five-card omission.
- Attack still passes because examples/overview text retained enough information for the model to reconstruct it.

### False-rules r2

- **R04:** It follows the planted false Skip rule: one Skip immediately clears all outstanding attacked turns and advances to the next player. Canonically, one Skip should consume only one owed turn.
- **R10:** It follows the planted false optional-Defuse sentence and exposes `explode:voluntarily` while Defuse is held.
- **R13:** It follows the planted false Kitten-retrieval trigger. Retrieving a Kitten enters a Defuse/explosion path instead of safely adding it to hand.
- **R12:** The resolution code comments that a newly discarded component may be taken, but legal-action generation still requires a pre-existing discard target. The intended interpretation is canonical, but the implementation does not make it executable.
- **R14/R15:** Empty Favor/pair targets remain legal no-ops.
- **Important counterexample:** The planted false Attack says three turns and additive chaining, but r2 implements canonical two-turn replacement instead. It likely privileged the unchanged example or prior structural expectation over the injected card text. The pilot implementation followed the false Attack more closely.
- The planted four-card/reorder Preview and forced-top Defuse reinsertion are not covered by the current 17 scenarios and must not be claimed correct.

### Vague-rules r2

- **R09:** The implementation explicitly documents its choice for “verlagert oder erweitert ... angemessen”: it carries unfinished debt forward and adds two (`remaining + 2`). From debt 2, chained Attack therefore produces 3, while our approved adjudication requires replacement with exactly 2.
- **R12:** It interprets the heading “Fünfling” as exactly five distinct titles, but still requires a retrieval candidate to exist before those five cards enter discard. Self-retrieval is unavailable.
- **R13:** It deliberately excludes Exploding Kitten from ordinary five-card retrieval candidates because “Besondere Karten ... entsprechend” is vague. Our adjudication permits safe retrieval.
- **R14/R15:** Empty opponents are exposed as legal targets and become no-ops.
- **R16:** Triple requests are generated from ordinary card-count keys plus Defuse, excluding Exploding Kitten; the model treated the hazard as outside the requestable card catalog.
- **Correctly handled:** A simple Attack is concretized as two turns, Preview/Shuffle/Favor keep the turn, two Skips consume two turns, Defuse is mandatory, and Cat pair executes. Thus the vague r2 result is much better than the vague pilot but still contains visible ambiguity choices.

## Pilot failures, for comparison

| Pilot condition | Failed IDs under the same v2.4 evaluator |
|---|---|
| Original PDF | R04, R12, R14, R15, R17 |
| Faithful TXT | R10, R14, R15 |
| Anonymized | R10, R14, R15, R16 |
| Omissions | R10, R12, R13, R16 |
| False rules | R03, R04, R09, R10, R11, R13, R14, R15, R16 |
| Vague rules | R03, R04, R05, R06, R07, R09, R12, R13, R14, R15, R16, R17 |

The paired changes are generation variance plus workflow change, not a clean causal estimate: each condition has one pilot and one r2 implementation.

## Failure attribution summary

| Failure pattern | Best current attribution |
|---|---|
| Optional Defuse in PDF/TXT | Source wording ambiguity interpreted literally by generator |
| Optional Defuse in false-rules | Planted false source rule followed |
| Missing five-card self-retrieval in PDF/TXT | Implementation ordering/legal-action defect |
| Missing Fünfling in omissions | Deliberate source-omission response |
| Skip clears all debt in false-rules | Planted false source rule followed |
| Retrieved Kitten explodes in false-rules | Planted false source rule followed |
| Additive chained Attack in vague | Explicit generator choice for vague wording |
| Empty targets in five r2 modules | Repeated implementation/adjudication-boundary choice |
| Anonymized v2.2/v2.3 false failures | Evaluator semantic-alias defect, fixed in v2.4 |
| TXT/vague Attack false failures in v2.2/v2.3 | Evaluator reaction-pass collision, fixed in v2.4 |
