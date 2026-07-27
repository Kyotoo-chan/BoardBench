# Rule coverage

Only the supplied two-page German rulebook is used as behavioral evidence. Contract/profile
items below concern representation only.

| Source section / named rule | Implementing symbol | Source-only probe or reason not probed | Assumption |
|---|---|---|---|
| So funktioniert's; explode/last survivor | `_draw`, `is_terminal`, `returns` | Self-check rollouts and terminal action check | none |
| Spielaufbau 1–7 | `initial_state`, `_shuffle`, `Game.__init__` | Seed repeatability, hand/deck/card counts, 2-player Defuse variant | Start player fixed to profile's evaluator default P0 |
| Spielzug: passen/spielen, then draw | `legal_actions`, `apply_action`, `_draw` | Every returned action applied by self-check | none |
| Clockwise continuation | `_alive_after`, `_finish_turn` | Eliminated-player skipping probe | none |
| No hand limit; deck may be counted | Hand lists; observation `deck_size` | Serialization/observation checks | none |
| Spielende | `_draw`, `returns`, terminal phase | Terminal state has no legal actions | Winner +1, eliminated players -1 is evaluator scoring representation |
| Beispielzug | normal play/reaction/draw transitions | Covered through constituent cards | none |
| Exploding Kitten (4) | `_draw` | Defused and undefused draw probes | none |
| Entschärfung (6); secret reinsertion | `defuse_reinsert`, `reinsert` actions | All 0..deck-size positions legal | Other players observe neither chosen position nor deck order |
| Angriff (4) | `_resolve` | Attack ends turn without draw and assigns two turns | A-02 |
| Hops! (4) | `_resolve`, `_finish_turn` | Skip decrements one owed turn | none |
| Wunsch (4) | `favor_give`, `give_card` | Target may give every card actually held | none |
| Mischen (4) | `_shuffle` | Seeded shuffle counter and round trip | none |
| Blick in die Zukunft (5) | player `preview`, `observation_to_data` | Own preview top-to-bottom; hidden from opponents | none |
| NÖ! (5), NÖ! on NÖ!, out-of-turn | `reaction`, `play_nope`, `pass_nope` | Reaction chain parity and discard behavior | A-01 |
| Katzen-Karten (4 jeder Art) | setup inventory; combinations | Count probe | Individually unplayable because source calls them powerless alone |
| Pärchen | `play_pair` | Any identical title accepted; random steal from nonempty hand | A-03 |
| Drilling | `play_triple` | Requested present/absent probes | none |
| Fünfling | `play_five` | Five distinct titles; retrieval from discard | Retrieval chooses a named matching discard card; identical copies are behaviorally equivalent |
| Combination instructions supersede card text | combination resolvers | Combination cards discarded without individual effects | none |
| Private hands / secret deck / secret reinsertion | `observation_to_data`, privileged state payload | Opponent hands and deck identities omitted | none |
| Canonical state/action/observation envelopes | serialization methods | `profile_fixture_self_check.py` | representation only |

## Explicit unresolved/non-material presentation gaps

- The source suggests humorous criteria for choosing a start player but defines no deterministic
  procedure. The profile explicitly supplies player 0 as the API default.
- The source does not define a numerical payoff scale. `returns` uses the conventional evaluator
  distinction +1 winner / -1 others; this does not alter gameplay, legality, or winner identity.
