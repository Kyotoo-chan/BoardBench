## Ambiguity/specification review

The implementation largely follows the canonical rules and approved geometric interpretations. The material source issues are concentrated in passing, positions with no legal movement, non-victory endings, and optional clocks.

### Ambiguous rule

#### 1. Whether a player may voluntarily pass

- **Page 1 quote:** “In ihrem Zug dürfen Sie nur eine ‚Bewegung‘ vornehmen – eigene Kugeln verschieben.”
- **Plausible interpretations:**
  1. A player must perform exactly one legal movement each turn.
  2. “Dürfen … nur eine” means at most one movement, so making no movement could be allowed.
- **Implementation choice:** Only `"move"` actions are generated; there is no voluntary-pass action. See [implementation.py:64](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:64) and [implementation.py:85](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:85).
- **Affected behavior:** Legal action set and turn progression whenever a player has at least one movement but would prefer not to make it.
- **Approved resolution:** Yes. The approved BoardBench convention states: “No voluntary pass is legal while at least one movement exists.” This is an approved interface convention, though not one of the separately dated “Human decision” bullets.
- **Clarification:** “A player who has at least one legal movement must make exactly one movement and may not pass.”

### Missing rules

#### 2. What happens when the active player has no legal movement

- **Pages 1 and 4 quotes:** “Die Spieler sind abwechselnd an der Reihe.” The only printed terminal rule is: “Der Spieler, der zuerst sechs Kugeln des Gegners hinaus geschoben hat, gewinnt das Spiel!”
- **Plausible interpretations:**
  1. The immobilized player passes and the opponent takes the next turn.
  2. The game ends, possibly as a loss or draw.
  3. Such a state is assumed impossible, leaving no prescribed behavior.
- **Implementation choice:** `legal_actions()` returns an empty tuple, but the state is nonterminal and `current_player()` still identifies the immobilized player. There is no pass transition, producing a deadlocked state. See [implementation.py:45](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:45), [implementation.py:64](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:64), and [implementation.py:135](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:135).
- **Affected behavior:** Available legal actions, state progression, current-player information, and potentially the terminal result.
- **Approved resolution:** Yes. The dated human decision requires exactly one forced pass if and only if no legal movement exists.
- **Assessment:** This began as a source omission, but the approved human decision resolves it for BoardBench. The implementation does not implement that resolution.
- **Clarification:** “If the active player has no legal movement, that player must pass; the game remains nonterminal and the opponent becomes active.”

#### 3. Draws, repetition, and other non-victory endings

- **Page 4 quote:** “Der Spieler, der zuerst sechs Kugeln des Gegners hinaus geschoben hat, gewinnt das Spiel!”
- **Source silence:** No rule covers repetition, an agreed draw, move limits, perpetual positions, or other non-victory endings.
- **Plausible interpretations:**
  1. Sixth ejection is the only terminal condition; play may continue indefinitely otherwise.
  2. Repetition, mutual agreement, immobilization, or an external tournament convention may produce a draw.
- **Implementation choice:** A state is terminal only when either ejection count reaches six. No repetition history or draw result exists. See [implementation.py:135](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:135) and [implementation.py:139](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:139).
- **Affected behavior:** State history, terminal detection, and terminal returns in long or cyclic games.
- **Approved resolution:** No new human rule supplies a draw condition. The approved facts deliberately leave this unresolved and unscored; the core-environment convention adds no draw or repetition result.
- **Clarification:** “Apart from the sixth ejection, the untimed game has no automatic draw, repetition, or move-limit ending.”

#### 4. Clock operation and timeout result

- **Page 4 quote:** “Wie beim Schach kann jedem Spieler eine bestimmte Spielzeit zugeteilt werden, zum Beispiel 10 oder 15 Minuten.”
- **Plausible interpretations:**
  1. Each player receives a total chess-clock allocation for the whole game.
  2. The stated time is a per-move limit.
  3. Time expiration immediately loses the game, forfeits the turn, or invokes tournament-specific adjudication.
- **Implementation choice:** No clock state, timed action, or timeout terminal result is implemented.
- **Affected behavior:** State information, action timing, turn progression, and terminal results.
- **Approved resolution:** Yes. The dated human decision excludes timed play and all timeout outcomes from the environment.
- **Clarification:** “Timed play is an optional external tournament rule; this rule set does not define clock operation or the consequence of time expiration.”

### Contradictory rules

There is no unresolved material contradiction in the approved packet.

The closest apparent conflict is:

- **Page 3:** a Sumito requires “hinter der oder den angegriffenen Kugeln eine freie Mulde”.
- **Page 4:** “Eine Kugel ist aus dem Spiel, wenn sie aus dem Spielfeld hinaus auf den Rand geschoben wird.”

Read literally, the first could prohibit an edge push because no playable pit exists behind the defender. Page 4 and Figure 8 supply the specific edge exception. The approved facts explicitly resolve this, and the implementation follows it by accepting an off-board cursor and incrementing the ejection count at [implementation.py:92](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:92) and [implementation.py:120](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:120).

A sufficient clarification would be: “For an on-board Sumito the pit behind the defenders must be empty; at the board edge, outside the board counts as available and the outer defender is ejected.”

### Merely untestable or interface-level matters

- **Social color lottery:** Page 1 says, “Losen Sie aus, welcher Spieler welche Farbe erhält.” The implementation models colors, not human identities, and always starts color index 0/Black. The approved facts allow deterministic environment assignment, so this is not a rules defect; the physical/social lottery itself is not represented.
- **Clock expiration:** It is untestable because clocks are absent and expressly excluded.
- **Coordinate and action names:** Axial coordinates, direction labels, tuple serialization, and numeric returns are BoardBench conventions rather than printed rules. Their chosen forms at [implementation.py:5](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:5), [implementation.py:7](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:7), and [implementation.py:154](C:/Users/benti/AppData/Local/Temp/boardbench_abalone_codex_ag_ambiguity_bcejp1bb/implementation.py:154) do not resolve or violate a printed-rule ambiguity.
- **Malformed simultaneous-six state:** `returns()` favors White if both ejection counters are already at least six. Such a state cannot arise through a legal atomic move, so the rulebook need not define it and it is not a material reachable ambiguity.

## Material-assumption summary

The implementation assumes mandatory movement, no voluntary pass, no draw or repetition ending, no clock, deterministic color-role representation, and edge ejection as the exception to the free-pit Sumito condition. All but one are consistent with the approved facts or conventions. The material mismatch is the no-legal-movement case: the approved human decision requires a forced pass, while the implementation instead leaves the game nonterminal with no available action.