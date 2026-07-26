# Rule coverage

The implementation uses only the supplied German rulebook (pages 1–2). The
profile and contract determine serialization, not behavior.

| Source section / named rule | Implementing symbol | Source-only probe or reason not probed | Assumption |
|---|---|---|---|
| Das Spiel / contents: 3–6 players, 60 cards | `Game.__init__`, `_inventory` | Constructor counts and inventory exercised by both self-checks | None |
| Die Aufgabe: predict exact tricks; score objective | `legal_actions`, `apply_action`, `_finish_trick` | Full rollouts exercise predictions, tricks, and scores | None |
| Die Vorbereitung: trustee/dealer, shuffle and deal | `initial_state`, `_deal_round` | Seed reproducibility and deal sizes checked locally | A-01, A-02 |
| Die Charakterkarten: four suits, 1–13, four Wizards, four Fools | `SUITS`, `RANKS`, `_inventory`, `_valid_card` | Inventory count probe | None |
| Das Verteilen der Karten: round N deals N; undealt stack; dealer rotates clockwise | `_deal_round`, `_finish_trick` | Full rollout and per-count terminal round probe | A-02 |
| Der Trumpf: reveal top stack card; suit is trump; Fool means none; Wizard lets dealer choose; final round none | `_deal_round`, `legal_actions`, `apply_action` | Wizard/Fool/ordinary/final-round branches directly represented; fixture check covers pending choice | “Top” is the end popped from the shuffled internal list, with no behavioral distinction after shuffle |
| Die Vorhersage: left of dealer, clockwise, recorded, repeat before first trick | `legal_actions`, `apply_action`, observation players | Rollout verifies every player predicts before play; verbal repetition has no game-state effect | A-02 |
| Der Kampf um den Stich: left of dealer leads; clockwise; must follow; may discard/trump if unable | `legal_actions`, `apply_action` | Legal-action filtering exercised during rollouts | A-03 |
| Attention: Wizards/Fools always playable; a played suit still must be followed | `legal_actions` | Source-only constructed-state probe implicit in legal-action implementation | None |
| Highest card wins; trump beats other suits; winner leads next | `_finish_trick` | Full rollouts | None |
| First round has only one trick | Round-size deal in `_deal_round` | Full rollout | None |
| Winner hierarchy: first Wizard; highest trump; otherwise highest led suit | `_finish_trick` | Source-only branch inspection and rollout | None |
| Special rights: after Wizard lead, arbitrary cards; first Wizard wins | `legal_actions`, `_finish_trick` | Constructed fixtures are accepted; branch encoded directly | None |
| Fool lead: second card determines required color; Fools lose | `apply_action`, `_finish_trick` | Color is set by the first later ordinary suited card | A-03 |
| All-Fool exception: first Fool wins (3–4 players only possible) | `_finish_trick` | Direct branch inspection; not guaranteed in random rollout | None |
| Erfahrungspunkte: exact = 20 + 10/trick; miss = −10 per difference | `_finish_trick` | Full rollouts; formula directly encoded | None |
| Worked scoring example (Thomas/Ute/Kevin) | `_finish_trick` | Formula yields the stated 20/30/20 then 10/10/20 cumulative values | None |
| Das Ende: all 60 cards dealt; rounds 10/12/15/20; highest score wins | `max_round`, `_finish_trick`, `is_terminal`, `returns` | Per-count max round encoded and rollouts terminate | Returns expose final experience scores; callers can determine tied/co-high winners |
| Variants: Plus/minus Eins, Verdeckter Tipp, Geheime Vorhersage, Hellsehen, Einfarbig | Not implemented (`configuration.variant` is profile-required `"base"`) | Explicit task/profile scope is base game; no variant action vocabulary exists | None |

No card or combination names beyond ordinary suit/rank cards, Wizard
(`zauberer`), and Fool (`narr`) occur in the supplied base rules.

