# TODO

Human thesis review (not for agents to auto-update on every game switch):

- Read each generated `outputs/<game>_*.py` carefully. Be able to explain why the BoardBench API requires each function and what trade-offs the model made.
- For every file in `checks/`, know what it tests and what a pass/fail means (`01`–`04` smoke/API, `05` random rollouts, `06` action-language sampling, `90` saved judge score, `99` OpenSpiel compare, `compare_pair` lockstep variants).
- Add rulebook-derived scenario/regression checks only after that code and check review, not while still exploring a new game.

Optional later:

- Provide complete finished game implementations as examples so a model can implement a new game better.
