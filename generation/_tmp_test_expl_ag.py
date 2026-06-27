import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outputs"))
from expl_gpt_ag import Game  # noqa: E402

g = Game()
rng = random.Random(0)
for rollout in range(3):
    state = g.initial_state()
    for step in range(20):
        actions = g.legal_actions(state)
        if not actions:
            break
        a = rng.choice(actions)
        try:
            state = g.apply_action(state, a)
        except Exception as exc:
            print(f"rollout {rollout+1} step {step+1} action {a!r}: {exc}")
            break
    else:
        print(f"rollout {rollout+1}: ok through 20 steps")
