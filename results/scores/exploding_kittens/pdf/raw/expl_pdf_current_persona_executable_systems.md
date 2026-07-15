## Code defects

### 1. Defuse incorrectly discards a remaining Attack turn

- Fact IDs: `DEF-04`, `SKIP-02`, `ATK-01`, `ATK-03`
- Evidence type: approved fact plus rulebook text
- Page: 2
- Quote: “Dann ist dein Spielzug beendet.” Approved clarification: any further turn owed by Attack must still be taken.
- Code: [implementation.py:136](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:136)
- Expected: If a player owes two turns and Defuses during the first, reinsertion ends only that individual turn. The same player must then take the remaining turn.
- Actual: Every insertion sets `player` to the next living player and `turns_left=1`, silently deleting the remaining obligation.
- Severity: Critical
- Confidence: High

### 2. Triple request is chosen after the Nope window and reveals the target’s hand

- Fact IDs: `TRI-01`, `TRI-02`, `NOPE-06`, `SET-08`
- Evidence type: approved facts plus rulebook text
- Page: 2
- Quotes: “dass du dir eine Karte von dem Mitspieler wünschen darfst”; the approved timing requires the requested title before the reaction window.
- Code: [implementation.py:71](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:71), [implementation.py:127](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:127), [implementation.py:171](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:171)
- Expected: The actor announces both target and requested title, then the complete proposal enters the Nope/Doch window. An unavailable named title simply transfers nothing.
- Actual: The pending tuple contains no requested title. Only after reactions does the actor enter `triple`, where legal actions enumerate the target’s actual titles plus a generic “not present” option. This leaks private hand contents and prevents a specific absent title from being announced.
- Severity: Critical
- Confidence: High

### 3. Restored transfer actions fail when the target spent its last card as Nope

- Fact IDs: `NOPE-02`, `NOPE-06`, `NOPE-07`, `FAV-01`, `PAIR-01`
- Evidence type: approved human adjudication plus implementation transition analysis
- Page: 2
- Quote: If a legal target spends its last card during the Nope/Doch chain and the action is restored, it resolves without a transfer.
- Code: [implementation.py:69](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:69), [implementation.py:124](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:124), [implementation.py:144](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:144)
- Expected: Resolution succeeds as a no-transfer result.
- Actual:
  - Restored Favor enters `favor` with an empty target and produces no legal donation action, deadlocking the game.
  - Restored Pair calls `random.choice([])`, raising an exception.
- Severity: Critical
- Confidence: High

### 4. Five-card combinations cannot retrieve a newly discarded component

- Fact IDs: `FIVE-01`, `NOPE-06`, `COMBO-01`
- Evidence type: approved corrected adjudication plus rulebook text
- Page: 2
- Quote: “darfst du dir eine beliebige Karte aus dem Ablagestapel nehmen.” The correction explicitly permits retrieving one of the five just-played cards.
- Code: [implementation.py:89](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:89), [implementation.py:175](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:175)
- Expected: Retrieval choices are drawn from the discard as it will exist after the five components are discarded. With an initially empty discard, the player may still select one of those components.
- Actual: Legal actions enumerate only the pre-existing discard. With an empty discard, no five-card action exists at all.
- Severity: Major
- Confidence: High

### 5. Exploding Kittens and Defuses are prohibited from same-title combinations

- Fact IDs: `PAIR-01`, `TRI-01`, `FIVE-02`
- Evidence type: approved facts
- Page: 2
- Quotes: “ALLE gleichen Karten als Pärchen”; the approved `FIVE-02` decision explicitly says a retrieved Kitten may participate in same-title combinations.
- Code: [implementation.py:84](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:84)
- Expected: Two equal titles form a pair and three equal titles form a triple. A Kitten held through discard retrieval does not explode and may be used this way.
- Actual: Both pair and triple generation explicitly reject `EK` and `DEFUSE`.
- Severity: Major
- Confidence: High for Kittens; medium-high for Defuses because `PAIR-01` says any same title without an exception.

### 6. Shuffle leaves stale preview knowledge marked as current

- Fact IDs: `FUT-01`, `FUT-03`, `SHUF-01`
- Evidence type: approved fact plus rulebook text
- Page: 2
- Quote: “Misch den Spielstapel sorgfältig neu.” Approved clarification: an earlier preview becomes stale and must not be presented as current knowledge.
- Code: [implementation.py:120](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:120), [implementation.py:122](C:/Users/benti/AppData/Local/Temp/boardbench_expl_pdf_current_executable_systems__cf_mp63/implementation.py:122)
- Expected: Resolving Shuffle invalidates every player’s cached top-card preview.
- Actual: Shuffle reorders `deck` but leaves `seen` unchanged.
- Severity: Major
- Confidence: High

## Source gaps and evaluator questions

- Player-specific observations are not defined. `GameState` exposes complete hands, deck order, and every `seen` entry to any caller, while `render()` hides hand and deck identities. Whether direct state access itself counts as a hidden-information violation is therefore an evaluator/API question, not classified above as a code defect.
- Exact physical Nope timing and priority remain explicitly non-hard-testable. The deterministic reaction cycle should not be rejected solely for choosing a particular priority order.
- The approved material does not require a precise shuffle distribution; only identity preservation and invalidation of prior knowledge are testable.
- Exact action encoding and the finite title domain offered for a triple request are interface choices, but the requested title must still be captured before reactions and must not be derived from the target’s private hand.

## Deterministic regression candidates

1. Construct an attacked player with `turns_left=2`, top card Kitten, and one Defuse. Draw, reinsert, and assert the same player remains active with `turns_left=1`.
2. Play a triple against a target holding one known card and assert the pending action already contains both target and requested title before any reaction.
3. Assert triple request actions do not enumerate the target’s hand and permit a named title the target lacks.
4. Target a one-card `NÖ!` hand with Favor; cancel and restore the action. Assert resolution returns to the actor without transfer and exposes a normal turn action set.
5. Repeat candidate 4 with a Pair and assert no exception and no transfer.
6. Give the actor five distinct titles with an empty discard. Assert a five-card combination can retrieve one of its own components after the reaction window.
7. Put two retrieved Exploding Kittens in hand and assert legal Pair actions exist; repeat with three for Triple.
8. Seed `seen` for multiple players, resolve an uncancelled Shuffle, and assert all cached previews are invalidated.
9. Preview a two-card and an empty draw pile and assert `FUT-01` returns respectively two and zero cards without error.
10. Eliminate an attacked player on the first owed turn and assert their remaining obligation disappears, clockwise play advances, and terminal state occurs immediately if only one player remains.