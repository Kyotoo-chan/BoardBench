# Wizard Version 1.0 source coverage

Only the supplied publisher rulebook's base game is implemented. Probes are the two supplied neutral self-checks plus rollout behavior exercised there.

| Source section / named rule or card | Implementing symbol(s) | Probe / status | Assumption |
|---|---|---|---|
| Title, players 3–6, 60 character cards | `Game.__init__`, `_deck` | constructor and inventory fixture probes | none |
| Es war einmal … | — | narrative, no mechanic | none |
| Die Aufgabe: predict exact tricks; most points wins | `legal_actions`, `apply_action`, `returns` | rollout and canonical round trips | A-02 return representation |
| Die Vorbereitung: scorekeeper, shuffle, deal | `initial_state`, `_shuffle`, `_deal` | seeded initial states and fixture checks | A-01 first dealer/deal order |
| Die Charakterkarten: Menschen/blau, Elfen/grün, Zwerge/rot, Riesen/gelb; ranks 1–13 | `SUITS`, `RANKS`, `_deck`, `_card_ok`, `_suit` | inventory and serialization checks | none |
| Four Zauberer, always trump, above 13 | `_deck`, `_finish_trick` | rollout; source-only winner logic inspection | none |
| Four Narren, never trump, below 1 | `_deck`, `_finish_trick` | rollout; source-only winner logic inspection | none |
| Das Verteilen: round N deals N cards; all cards in final round | `_deal`, `_finish_round`, `max_round` | 3–6 constructors and rollout | A-01 |
| Dealer passes clockwise to player on left | `_finish_round` | source-only transition inspection | player indices increase clockwise (part of A-01) |
| Undealt cards form face-down center deck | `_deal`, state `zones.deck` | canonical zone fixture | none |
| Der Trumpf: reveal top deck card | `_deal` | rollout and canonical state | none |
| Ordinary reveal sets trump suit | `_deal` | rollout | none |
| Revealed Narr means no trump | `_deal` | source-only branch inspection | none |
| Revealed Zauberer: dealer chooses after seeing hand | `_deal`, `choose_trump` actions | phase/pending fixture and rollout | none |
| Final round has no revealed card/no trump | `_deal` | source-only branch inspection | none |
| Die Vorhersage: starts left of dealer, clockwise, visible | `_deal`, `predict` actions, `observation_to_data` | rollout and observation schema | none |
| Prediction range permitted by cards/tricks in round | `legal_actions` (`0..round_number`) | rollout | inferred directly from “how many tricks … in this round” |
| Der Kampf: left of dealer leads first; subsequent winner leads | `_deal`, `_finish_trick` | rollout | none |
| Follow first ordinary suit when possible; otherwise discard/trump | `legal_actions`, `led_suit` | rollout | none |
| Zauberer/Narr may always be played and do not have to follow | `legal_actions` | rollout/source-only inspection | none |
| Highest trump, else highest led suit wins | `_finish_trick` | rollout/source-only inspection | none |
| First Zauberer wins, including multiple Zauberer | `_finish_trick` | source-only inspection | none |
| Zauberer led allows any following card | `led_suit`, `legal_actions` | source-only inspection | none |
| Narr led: second ordinary card establishes suit | `apply_action` led-suit update | source-only inspection | none |
| Narren lose; all-Narr trick won by first Narr | `_finish_trick` | source-only inspection | none |
| Scoring exact: 20 + 10 per won trick | `_finish_round` | rollout/source-only inspection | none |
| Scoring miss: −10 per trick above/below prediction | `_finish_round` | rollout/source-only inspection | none |
| Scoring examples, rounds 1 and 2 | `_finish_round` | examples map exactly to formula; no separate fixture | none |
| Das Ende: rounds 10/12/15/20 for 6/5/4/3; final scored; highest score wins | `max_round`, `_finish_round`, `is_terminal`, `returns` | constructors/rollout | A-02 |
| Varianten: Plus/minus Eins | — | explicitly out of scope by `TASK.txt`; not implemented | none |
| Varianten: Verdeckter Tipp | — | explicitly out of scope; not implemented | none |
| Varianten: Geheime Vorhersage | — | explicitly out of scope; not implemented | none |
| Varianten: Hellsehen | — | explicitly out of scope; not implemented | none |
| Varianten: Einfarbig (3/4 players), including its combinations and 12-round ending | — | explicitly out of scope; not implemented | none |
| Publisher/contact/version footer | — | metadata, no mechanic | none |
| Canonical complete state/action profile | `state_to_data`, `state_from_data`, `action_to_data`, `action_from_data` | both supplied self-checks | representation contract, not rule source |
| Private hands/public observation | `observation_to_data` | neutral observation checks | none |
| Stable reversible human names | `action_to_name`, `name_to_action` | agentic self-check | none |
