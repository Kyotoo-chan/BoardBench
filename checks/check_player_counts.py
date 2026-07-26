#!/usr/bin/env python3
"""Hard-check every source-supported player count from an environment profile."""

from __future__ import annotations

import argparse
import inspect
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from checks.common import CheckContext, import_generated_module, legal_actions, random_rollout, suppress_generated_output


def check_player_counts(code: Path, profile_path: Path, *, max_steps: int = 100) -> dict:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    specification = profile.get("player_counts")
    if not isinstance(specification, dict) or not specification.get("supported"):
        raise ValueError("profile needs player_counts.supported")
    supported = specification["supported"]
    if any(not isinstance(count, int) or count < 1 for count in supported) or len(supported) != len(set(supported)):
        raise ValueError("supported player counts must be unique positive integers")
    unsupported = specification.get("unsupported", [min(supported) - 1, max(supported) + 1])
    unsupported = [count for count in unsupported if count >= 0 and count not in supported]

    ctx = CheckContext(Path(__file__).resolve().parents[1], code.stem, code.resolve(), 1, max_steps, 1)
    module = import_generated_module(ctx)
    game_cls = getattr(module, "Game")
    if "num_players" not in inspect.signature(game_cls).parameters:
        raise AssertionError("Game constructor has no num_players parameter")

    results = []
    for count in supported:
        try:
            with suppress_generated_output():
                parameters = inspect.signature(game_cls).parameters
                kwargs = {"num_players": count}
                if "seed" in parameters:
                    kwargs["seed"] = 1
                game = game_cls(**kwargs)
                state = game.initial_state()
            if not game.is_terminal(state) and not legal_actions(game, state):
                raise AssertionError("initial non-terminal state has no legal actions")
            error = random_rollout(game, state, random.Random(count), max_steps)
            if error:
                raise AssertionError(error)
        except Exception as exc:
            results.append({"count": count, "status": "FAIL", "message": f"{exc.__class__.__name__}: {exc}"})
        else:
            results.append({"count": count, "status": "PASS", "message": ""})

    for count in unsupported:
        try:
            with suppress_generated_output():
                game_cls(num_players=count)
        except ValueError:
            results.append({"count": count, "status": "PASS", "message": "rejected"})
        except Exception as exc:
            results.append({"count": count, "status": "FAIL", "message": f"expected ValueError, got {exc.__class__.__name__}"})
        else:
            results.append({"count": count, "status": "FAIL", "message": "unsupported count accepted"})

    return {
        "supported": supported,
        "unsupported": unsupported,
        "passed": sum(item["status"] == "PASS" for item in results),
        "total": len(results),
        "results": results,
        "note": "count-specific setup quantities remain hard scenario claims",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-path", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    try:
        result = check_player_counts(args.code_path, args.profile, max_steps=args.max_steps)
    except Exception as exc:
        print(f"FAIL player-count check: {exc}")
        return 1
    for item in result["results"]:
        suffix = f": {item['message']}" if item["message"] else ""
        print(f"{item['status']} players={item['count']}{suffix}")
    print(f"PLAYER_COUNTS {result['passed']}/{result['total']}")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if result["passed"] == result["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
