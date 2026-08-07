import json, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from checks.common import CheckContext, make_game
from checks.run_scenarios import ScenarioUnreached, ScenarioUntestable
from checks.run_scenarios_v4 import _load_adapter, load_suite, run_scenario_v4

code = root / (sys.argv[2] if len(sys.argv) > 2 else "outputs/bohnanza_base_2023_codex_ag.py")
suite = load_suite(root / "checks/scenarios/bohnanza_base_2023_v2.json", root)
scenario = suite["scenarios"][int(sys.argv[1])]
ctx = CheckContext(root, suite["game"], code, 1, 1, 1)
module, game, _ = make_game(ctx)
adapter = _load_adapter(suite, root)
try:
    run_scenario_v4(game, scenario, module, adapter)
except ScenarioUnreached as error:
    status, detail = "UNREACHED", str(error)
except ScenarioUntestable as error:
    status, detail = "UNTESTABLE", str(error)
except AssertionError as error:
    status, detail = "FAIL", str(error)
except Exception as error:
    status, detail = "CRASH", f"{error.__class__.__name__}: {error}"
else:
    status, detail = "PASS", ""
print(json.dumps({"id": scenario["id"], "status": status, "detail": detail,
                  "basis": scenario["basis"], "fact_ids": scenario["fact_ids"]}))
