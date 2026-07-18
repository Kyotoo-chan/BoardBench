---
status: approved
game: bohnanza
condition: augmented_user_observation
rendered_and_reviewed: 2026-07-18
approved_by_user: 2026-07-18
sources:
  - id: RULES
    role: publisher_rulebook
    path: inputs/games/bohnanza/game_rules.pdf
    sha256: 11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d
    edition: "Bohnanza Grundspiel und Ackerbohne, German excerpt, 11 PDF pages"
  - id: COMPONENTS
    role: user_observation
    path: inputs/games/bohnanza/game_components.pdf
    sha256: 83b5db35b65975723190bb03b113751f43a48895e0a7f0cd546649f98df01ea4
    edition: "User-authored Kartenübersicht Grundspiel + Ackerbohne, 3 PDF pages"
---

# Approved Bohnanza rule facts

This is an **augmented source condition**. `RULES` governs gameplay. `COMPONENTS` may establish observed component identities and counts, but does not silently override gameplay rules. All pages below are PDF pages.

## Setup and inventory

| ID | Source | Page | Direct quote | Approved expectation | Basis |
|---|---|---:|---|---|---|
| SET-01 | RULES | 2 | “GRUNDSPIEL (3–5 SPIELER)” | Base game supports 3–5 players. The selected Ackerbohne condition supports 4–5. | clear |
| SET-02 | RULES | 2 | “Spielt ihr zu dritt … drei Bohnenfeldern … zu viert oder zu fünft … zwei Bohnenfeldern” | Three players start with three fields; four or five with two. | clear |
| SET-03 | RULES | 2 | “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.” | One configured/chosen start player acts first and keeps the marker. | clear |
| INV-01 | RULES | 2 | “Es gibt 104 Karten mit acht verschiedenen Bohnensorten.” | Base inventory is exactly 104 cards across eight types. | clear |
| INV-02 | RULES | 2 | Card-face large numbers: 6, 8, 10, 12, 14, 16, 18, 20 | Garten 6, Rote 8, Augen 10, Soja 12, Brech 14, Sau 16, Feuer 18, Blaue 20. | clear, diagram |
| INV-03 | RULES | 10 | “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen” | Ackerbohne variant includes all eight base types plus Ackerbohne and Weinbrandbohne. | clear |
| INV-04 | COMPONENTS | 1 | “Verwendet genau 129 Bohnenkarten: 104 aus dem Grundspiel, 22 Weinbrandbohnen und 3 Ackerbohnen.” | Selected 4–5-player deck has exactly 129 cards: base 104 + Weinbrand 22 + Acker 3. | user_observation |
| INV-05 | COMPONENTS | 3 | “Nicht in diesen Kartensatz legen” | Coffee, cocoa, order cards, Elsterbohnen, separate AMIGO coins, and other editions are excluded. | user_observation |
| HAND-01 | RULES | 3 | “verteilt an jeden Spieler einzeln fünf Handkarten” | Deal five ordered cards to each player. | clear |
| HAND-02 | RULES | 3 | “Die Reihenfolge … darfst du … nicht ändern … Du darfst die Karten nicht sortieren.” | Hand order is immutable; draws append at the back. | clear |
| HAND-03 | RULES | 3 | “Die erste verteilte Karte … ist die vorderste Karte.” | Front card is the next mandatory hand card. Owner sees the whole hand; opponents see only its count unless players voluntarily communicate. | human_decision |

## Turn and planting

| ID | Source | Page | Direct quote | Approved expectation | Basis |
|---|---|---:|---|---|---|
| TURN-01 | RULES | 4 | “Danach geht es im Uhrzeigersinn weiter.” | Turns proceed clockwise; start-player marker does not move. | clear |
| TURN-02 | RULES | 4 | “führst du nacheinander vier Phasen durch” | Hand planting; reveal/trade; mandatory planting; drawing, in that order. | clear |
| FIELD-01 | RULES | 4 | “Auf einem Feld darfst du nur Bohnen der gleichen Sorte anbauen.” | A field contains one type; one type may occupy multiple fields. | clear |
| P1-01 | RULES | 4 | “Du musst die vorderste Bohnenkarte … anbauen.” | First/front hand card is mandatory. | clear |
| P1-02 | RULES | 4 | “Danach darfst du eine weitere … Eine dritte Bohne darfst du nicht anbauen.” | Second front card is optional; third is forbidden in phase 1. | clear |
| P1-03 | RULES | 5 | “kein Feld dafür … musst du zuerst ein Feld abernten” | If a mandatory card cannot fit, harvest a legal field first. | clear |
| P1-04 | RULES | 5 | “keine Karten auf der Hand, gehst du gleich zur 2. Phase” | Empty hand skips phase 1. | clear |

## Reveal and trade

| ID | Source | Page | Direct quote | Approved expectation | Basis |
|---|---|---:|---|---|---|
| P2-01 | RULES | 5 | “Ziehe die obersten zwei Karten … für alle sichtbar” | Reveal two public cards for the active player. | clear |
| TRADE-01 | RULES | 5 | “Nur du als aktiver Spieler darfst mit anderen Spielern handeln.” | Every trade includes the active player; inactive players cannot trade together. | clear |
| TRADE-02 | RULES | 5 | “mit euren Handkarten handeln … wo sich die Karten auf der Hand befinden” | Any hand position may be traded without reordering remaining cards; active player may also trade reveals. | clear |
| TRADE-03 | RULES | 5 | “nach einem Handel … nicht weiterhandeln … auf Feldern … ebenfalls nicht” | Received and planted cards cannot be traded. | clear |
| TRADE-04 | RULES | 5 | “unterschiedlichen Kartenanzahl handeln” | Exchange quantities may differ. | clear |
| TRADE-05 | RULES | 6 | “beide Spieler müssen dem Handel zustimmen” | Trade is an atomic consensual transfer; cards stay put until accepted. | clear |
| TRADE-06 | RULES | 6 | “quer neben deinen Feldern … Auf die Hand nehmen darfst du sie nicht.” | Received cards wait outside the hand. | clear |
| TRADE-07 | RULES | 6 | “Bohnenkarten schenken … muss … zustimmen” | A nonempty gift is legal only with recipient consent. | clear |

## Mandatory planting and draw

| ID | Source | Page | Direct quote | Approved expectation | Basis |
|---|---|---:|---|---|---|
| P3-01 | RULES | 7 | “müssen diese nun anbauen … jede aufgedeckte Karte … nicht gehandelt” | All received cards and all retained reveals must be planted. | clear |
| P3-02 | RULES | 7 | “selbst entscheiden, in welcher Reihenfolge” | Each recipient chooses planting order and any necessary legal harvest between cards. | clear |
| P4-01 | RULES | 10 | “zieht jeder von euch eine Karte … aktive Spieler … im Uhrzeigersinn” | In the selected Acker variant, each player draws one, active player first clockwise, appending it. | clear |
| DECK-01 | RULES | 9 | “Ziehst du die letzte Karte … mische die Karten des Ablagestapels.” | On first/second depletion, immediately shuffle discard and continue any owed draw from the new pile; if no cards exist, the sequence stops. | human_decision |

## Harvesting and Ackerbohne

| ID | Source | Page | Direct quote | Approved expectation | Basis |
|---|---|---:|---|---|---|
| HARV-01 | RULES | 7 | “jederzeit … auch wenn du nicht der aktive Spieler bist” | Owner may harvest between individual game steps, including during another turn, but not inside an already executing atomic draw/transfer. | human_decision |
| HARV-02 | RULES | 8 | “Drehe so viele Karten … Bohnentaler … restlichen … Ablagestapel … Feld immer leer.” | Normal harvest flips earned cards to coins, discards the rest, and empties the field. | clear |
| HARV-03 | RULES | 8 | “keine einzelne Bohnenkarte ernten, wenn … einem deiner Felder mehr als eine” | A singleton cannot be harvested if any own field has 2+ cards; otherwise it may be. | clear |
| ACKER-01 | RULES | 11 | “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.” | Exactly two unlock field 3 if absent; both harvested cards are discarded, old fields 1–2 persist. | clear |
| ACKER-02 | RULES | 11 | “bereits ein drittes Bohnenfeld … erhältst du … nichts” | If field 3 already exists, two yield no reward but are normally discarded and the field empties. | human_decision |
| ACKER-03 | RULES | 11 | “drei Ackerbohnen … drei Bohnentaler” | Exactly three become three coins and do not unlock field 3. | human_decision |
| ACKER-04 | COMPONENTS | 2 | “1 Ackerbohne — 0 Taler — Normale Null-Ernte” | One Ackerbohne is a legal zero harvest when protection permits; discard it and do not unlock a field. | human_decision based on user observation |

## End and result

| ID | Source | Page | Direct quote | Approved expectation | Basis |
|---|---|---:|---|---|---|
| END-01 | RULES | 9 | “endet, sobald der Nachziehstapel zum dritten Mal leer wird” | At four/five players, the third depletion triggers the end. | clear |
| END-02 | RULES | 9 | “beim Aufdecken … spielt ihr die 2. und die 3. Phase noch zu Ende” | If third depletion occurs while revealing, finish phases 2 and 3, then score; phase 4 is skipped. | clear |
| END-03 | RULES | 9 | “Alle Spieler ernten noch … Karten auf der Hand zählen nicht” | Final harvest all fields; hands score zero; each coin card is one point. | clear |
| END-04 | RULES | 9 | “Bei einem Gleichstand … im Uhrzeigersinn am weitesten weg vom Startspieler” | Greatest clockwise seat distance from original start player wins among tied players. | clear |
| END-05 | RULES | 9 | “endet, sobald” | If third depletion occurs during variant phase 4, stop immediately after the draw that empties it; no remaining players draw, then final harvest and score. | human_decision |
| END-06 | RULES/COMPONENTS | — | No elimination mechanism appears. | No player is eliminated before final scoring. | human_decision |

## Approved corrections and conflict decisions — 2026-07-18

- `COMPONENTS` p.3 phrase “2 Karten = 2 [Taler]” is a transcription error. Two Ackerbohnen unlock field 3; they never award two coins.
- Conflicting Saubohne prose in `COMPONENTS` is a transcription error. `RULES` p.8 controls: 3–4 → 1, 5–6 → 2, 7 → 3, 8+ → 4 coins.
- The Ackerbohne condition is the 4–5-player 129-card augmented condition, not the 104-card base setup.

## Explicit executable conventions

- Trade proposals and accept/reject choices are explicit actions. No multi-party, contingent, delayed, or empty-for-empty trade is required.
- Harvesting is explicit between atomic steps. Mandatory planting order and forced-harvest target are explicit choices.
- State observations expose each player’s own whole ordered hand and only its count to opponents.
- Nonterminal returns are zero. Terminal returns may use winner-based `+1/-1` or a documented score-based equivalent, but raw coin totals must remain observable.

## Unresolved but intentionally unscored

- Exact packaged counts of non-bean mats/overview cards beyond one per participating player.
- Behavior in impossible evaluator-constructed states where both draw and discard piles contain too few cards before a nonterminal owed draw.
- Social negotiation language, voluntary revelation, conditional/multi-party promises, and timing inside an atomic action.

## Temporal boundaries

- A confirmed trade resolves fully before another harvest/action.
- Each mandatory planting is one step; harvest may occur between such steps.
- First/second pile depletion and reshuffle resolve before the remaining owed draw.
- Third depletion in phase 2 leaves trading and phase-3 planting pending; terminal scoring occurs only after they finish.
- Third depletion in phase 4 is immediately terminal before another player draws.
