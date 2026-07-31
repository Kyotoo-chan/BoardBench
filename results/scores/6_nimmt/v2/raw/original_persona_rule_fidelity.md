## Findings

All findings affect states imported through `state_from_data`; ordinary states created by `initial_state()` use the correct base-game setup.

### 1. Imported states can change the fixed match threshold

- Fact IDs: `6N-C-MATCH-THRESHOLD`, `6N-C-ALTERNATE-TARGET`
- Evidence type: `rule_quote`
- Page 2 quote: “Es werden mehrere Spiele durchgeführt, bis ein Spieler insgesamt über 66 Hornochsen eingesammelt hat.”
- Code: [implementation.py:287](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_rule_fidelity_jwvey4zd/implementation.py:287), [implementation.py:146](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_rule_fidelity_jwvey4zd/implementation.py:146)
- Expected: Under the declared base-game scope, the match ends after a completed game when a cumulative score is strictly greater than 66; exactly 66 continues.
- Actual: Deserialization accepts any integer `match_target`, including `0`, and `_finish_round()` uses that imported value. Thus an accepted “base” state can terminate at a noncanonical threshold.
- Severity: **Major**
- Confidence: **High**

### 2. Out-of-inventory cards become legal plays after deserialization

- Fact ID: `6N-M-CARD-IDENTITIES`
- Evidence type: `human_decision`
- Page: N/A — `canonical_supplement.json`, `/cards/identities`
- Direct quote: `{"kind":"integer_range","minimum":1,"maximum":104,"copies_each":1}`
- Code: [implementation.py:274](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_rule_fidelity_jwvey4zd/implementation.py:274), [implementation.py:300](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_rule_fidelity_jwvey4zd/implementation.py:300), [implementation.py:96](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_rule_fidelity_jwvey4zd/implementation.py:96)
- Expected: The deck contains exactly one card of every integer value 1–104.
- Actual: The deserializer defines a card as any Python integer. A hand containing card `105` is accepted, and `legal_actions()` subsequently offers `commit_card(105)` as a legal action.
- Severity: **Major**
- Confidence: **High**

### 3. Deserialization does not require exactly four rows

- Fact ID: `6N-C-FOUR-ROWS`
- Evidence type: `rule_quote`
- Page 1 quote: “Vom restlichen Kartenstapel legen Sie die obersten vier Karten offen untereinander in der Tischmitte aus.”
- Code: [implementation.py:316](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_rule_fidelity_jwvey4zd/implementation.py:316), [implementation.py:117](C:/Users/benti/AppData/Local/Temp/.ctx-mode-vm3Erx/boardbench_original_rule_fidelity_jwvey4zd/implementation.py:117)
- Expected: Play always has exactly four public rows.
- Actual: Any number of row lists is accepted. With five imported rows, ordinary placement considers all five when selecting the closest eligible row. With fewer than four, low-card actions still offer four indices and can fail when applied.
- Severity: **Major**
- Confidence: **High**

## Question

Is `state_from_data()` intended to accept only already-trusted snapshots? The canonical sources do not define a serialization trust model. Even under that interpretation, the function presents itself as a validator and accepts states whose subsequent behavior contradicts the canonical rules.

## Coverage

Covered rule areas included player range; 104-card setup; dealing and reserve; four-row setup; hidden commitments and joint reveal; ascending and dynamic resolution; closest-row placement; sixth-card and low-card captures; captured-card handling; bullhead values; ten-round game ending; cumulative scoring; new games; the greater-than-66 threshold; shared minimum-score winners; seeded lifecycle; observations; and terminal returns.

Uncovered or outside scope: professional play, optional target/game-count variants, strategy advice, and physical presentation details that have no distinct executable behavior.

Qualitatively, the normal game engine is strongly faithful to the supplied rules. The material weakness is the imported-state boundary: it can admit noncanonical cards, layouts, and match configuration, after which the engine treats them as playable base-game states.