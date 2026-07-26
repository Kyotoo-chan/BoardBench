# Rule coverage

| Supplied section / named rule | Implementing symbol | Source-only probe or reason not probed | Assumption |
|---|---|---|---|
| Es war einmal … | Module provenance only | No mechanic to probe | None |
| Die Aufgabe | `Game._finish_round`, `returns` | Exact prediction scores; terminal scores returned | None |
| Die Vorbereitung | `initial_state`, `_deal_round` | 60-card inventory and rotating dealer | A-01 |
| Die Charakterkarten: Menschen, Elfen, Zwerge, Riesen; ranks 1–13 | `SUITS`, `_cards`, `_valid_card` | Inventory contains every suit/rank once | None |
| Zauberer always trump / above 13 | `_trick_winner` | First Wizard wins regardless of later cards | None |
| Narr never trump / below 1 | `_trick_winner` | All-Narr trick goes to first Narr | None |
| Das Verteilen der Karten | `_deal_round` | Round N deals N cards; undealt cards stay in deck | None |
| Dealer duty passes clockwise | `_finish_round` | Dealer increments modulo player count | A-01 only for initial dealer |
| Der Trumpf: reveal top card | `_deal_round` | Ordinary card sets its suit | None |
| Revealed Narr means no trump | `_deal_round` | `trump_suit` remains null | None |
| Revealed Zauberer: dealer chooses | `choose_trump` phase/actions | Four source-labelled suit choices | None |
| Last round has no trump | `_deal_round` | Empty post-deal deck means no reveal/no trump | None |
| Die Vorhersage | `predict` phase/actions | Each player may predict 0 through round size, starting left of dealer | None |
| Der Kampf um den Stich: clockwise play | `apply_action` | Actor advances modulo player count | None |
| Must follow led suit | `legal_actions` | Off-suit ordinary cards excluded when player can follow | None |
| Wizard/Narr may always be played | `legal_actions` | Specials remain legal despite follow-suit | None |
| Highest trump, otherwise highest led suit | `_trick_winner` | Direct fixture probes supported by serialized states | None |
| Winner leads next trick | `apply_action` | Winner becomes leader/current player | None |
| First round has one trick | Round-size deal plus hand exhaustion | Natural rollout probe | None |
| Special rights: trick opened by Zauberer | `_trick_winner`, `legal_actions` | First Wizard wins; subsequent cards unrestricted because no led suit | None |
| Special rights: trick opened by Narr | `apply_action`, `legal_actions`, `_trick_winner` | First later ordinary card establishes suit; Narr loses unless all are Narren | None |
| Vergabe der Erfahrungspunkte | `_finish_round` | Exact: 20 + 10/trick; miss: −10 per difference | None |
| Example (Thomas/Ute/Kevin) | `_finish_round` | Arithmetic matches both example rounds | None |
| Das Ende (6:10, 5:12, 4:15, 3:20 rounds) | `max_round`, `_finish_round`, `is_terminal` | `60 // players`; terminal after final round | None |
| Variante Plus/minus Eins | Not implemented | Explicitly outside `configuration.variant = base` | None |
| Verdeckter Tipp | Not implemented | Variant, not base game | None |
| Geheime Vorhersage | Not implemented | Variant, not base game | None |
| Hellsehen | Not implemented | Variant, not base game | None |
| Einfarbig (3 or 4 players) | Not implemented | Variant, not base game | None |
| Private hands / public predictions | `observation_to_data` | Own hand shown; opponents expose only hand size; predictions public after made | None |
| Terminal states have no legal actions | `legal_actions` | Explicit terminal guard | None |
