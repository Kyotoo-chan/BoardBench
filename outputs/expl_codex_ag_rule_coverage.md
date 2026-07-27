# Rule coverage

Rule evidence is limited to the supplied two-page German rulebook. “Probe” names are compact source-only scenarios suitable for direct calls to the indicated symbols.

| Source section / named rule | Implementing symbol(s) | Source-only probe or unprobed reason | Assumption |
|---|---|---|---|
| SO FUNKTIONIERT'S; exploding player leaves; last survivor wins | `Game._draw`, `Game.is_terminal`, `Game.returns` | Draw a kitten without Entschärfung; verify elimination and then sole-survivor terminal result | A-03 for destination of eliminated inventory; A-05 for numeric returns |
| GRUNDSÄTZLICH; draw risk, other cards reduce risk | `Game.legal_actions`, `Game.apply_action` | Verify optional plays followed by mandatory `draw` to end an ordinary turn | None |
| SPIELAUFBAU 1–7 | `Game.initial_state`, `Game.__init__` | For 2–5 players, count inventory, 8-card hands, one Entschärfung each, player-count-minus-one kittens in deck, box remainder, shuffled deck, player 0 API default | Start-player criterion is intentionally represented by deterministic profile default |
| VARIANTE FÜR ZWEI SPIELER | `Game.initial_state` | Verify only two spare Entschärfung cards enter the two-player deck | None |
| SPIELZUG: Passen oder Spielen, dann Ziehen | `Game.legal_actions`, `Game._finish_turn` | Verify any number of legal plays remain in `play`, and drawing advances the turn | None |
| SPIELENDE; no hand limit; deck may be counted | `Game._draw`, `Game.is_terminal`, `Game.observation_to_data` | Large hands remain valid; observation exposes `deck_size`; sole survivor ends game | None |
| BEISPIELZUG | `Game._resolve_proposed`, `Game._draw` | See Future, Angriff, NÖ!, Mischen, then draw can be executed in the illustrated order | A-01 for reaction timing |
| EXPLODING KITTEN (4) | `Game._draw` | Immediate reveal modeled by immediate resolution; no Entschärfung eliminates player | A-03 |
| ENTSCHÄRFUNG (6); secret reinsertion | `Game._draw`, `Game.legal_actions`, `Game.apply_action`, `Game.observation_to_data` | Kitten plus Entschärfung enters `defuse_reinsert`; every deck position legal; position is absent from observations after resolution | None |
| NÖ! (5); cancels cards/actions except kitten/defuse; NÖ! on NÖ! | `Game._propose`, `Game._reset_responders`, `Game._finish_reaction` | Odd NÖ! count cancels, even count restores; playable out of turn; kitten/defuse are immediate and un-NÖ!-able | A-01 |
| ANGRIFF (4) | `Game._resolve_proposed`, `Game._finish_turn` | Ends without draw and next player owes two turns; victim's Angriff ends first owed turn and passes exactly two | A-02 |
| HOPS! (4) | `Game._resolve_proposed`, `Game._finish_turn` | Ordinary Hops ends turn without draw; under Angriff it consumes only one owed turn | None |
| WUNSCH (4) | `Game._resolve_proposed`, `Game.legal_actions` (`favor_give`) | Chosen target selects any card from own hand and transfers it; empty-hand target resolves without transfer | A-04 |
| MISCHEN (4) | `Game._resolve_proposed`, `Game._rng` | Seed/counter-identical states shuffle identically and change deck order | None |
| BLICK IN DIE ZUKUNFT (5) | `Game._resolve_proposed`, `Game.observation_to_data` | Actor alone sees top three in order via `preview`; preview clears on that actor's draw | Clearing time is representation bookkeeping, with no change to card knowledge already acquired |
| KATZEN-KARTEN (4 jeder Art); individually powerless | `Game._resolve_proposed`, `CAT_CARDS` | Single cat play has no effect after any NÖ! window | None |
| KOMBINATIONEN general; card instructions do not apply | `Game._propose`, `Game._resolve_proposed` | Combo consumes cards but never resolves their printed single-card effects | None |
| PÄRCHEN; any equal titles, steal random card | `Game.legal_actions`, `Game._resolve_proposed`, `Game._rng` | Every doubled title can target a living opponent; seeded random transfer | None |
| DRILLING; request a card, transfer iff held | `Game.legal_actions`, `Game._resolve_proposed` | Every tripled title/request/target action is offered; transfer succeeds iff present | None |
| FÜNFLING; five different titles, retrieve discard | `Game.legal_actions`, `Game._resolve_proposed` | Every five-title selection and currently discarded title can be selected | None |
| Terminal states have no actions (contract requirement) | `Game.legal_actions` | Terminal fixture returns `[]` | Evaluator representation, not an added game rule |
| Canonical state/action/observation and private hands | `state_to_data`, `state_from_data`, `action_to_data`, `action_from_data`, `observation_to_data` | Contract and profile round trips; opponent hands hidden as sizes | Evaluator representation only |
