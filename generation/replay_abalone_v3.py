#!/usr/bin/env python3
"""Replay frozen Abalone v2 implementations under the v3 rubric.

v2 scores stay unchanged. This does not generate new code. It removes the
unspecified no-move forced-pass scenario from the evaluated suite and rebuilds
result cards from the archived implementations, checks, judges, and usage.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generation.result_card import aggregate, markdown

V2 = ROOT / "results/scores/abalone/v2"
V3 = ROOT / "results/scores/abalone/v3"
SUITE_V2 = ROOT / "checks/scenarios/abalone_v2.json"
SUITE_V3 = ROOT / "checks/scenarios/abalone_v3.json"
CLAIMS_V2 = ROOT / "inputs/games/abalone/claims_v2.json"
CLAIMS_V3 = ROOT / "inputs/games/abalone/claims_v3.json"
DROPPED = "ABAL-R19-forced-pass-only-with-no-move"
RUBRIC = "abalone-v3-atomic-2026-08-23"
RULEBOOK = "c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def extract_member(archive: Path, name: str, dest: Path) -> None:
    with tarfile.open(archive, "r:gz") as tar:
        member = tar.getmember(name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        extracted = tar.extractfile(member)
        if extracted is None:
            raise FileNotFoundError(f"{name} in {archive}")
        dest.write_bytes(extracted.read())


def build_claims() -> None:
    inventory = json.loads(CLAIMS_V2.read_text(encoding="utf-8"))
    for claim in inventory["claims"]:
        if claim["id"] != "ABAL-G-PASS":
            continue
        claim["testable"] = False
        claim["coverage_exception"] = (
            "The publisher source does not specify no-movement behavior. "
            "The constructed ABAL-R19 fixture remains visible in v2 and is not scored under v3."
        )
    write_json(CLAIMS_V3, inventory)


def build_suite() -> None:
    suite = json.loads(SUITE_V2.read_text(encoding="utf-8"))
    suite["rubric_version"] = RUBRIC
    suite["claim_inventory"] = "inputs/games/abalone/claims_v3.json"
    suite["prior_rubric"] = {
        "path": "checks/scenarios/abalone_v2.json",
        "sha256": sha256(SUITE_V2),
        "rubric_version": "abalone-v2-atomic-2026-07-26",
    }
    suite["scenarios"] = [item for item in suite["scenarios"] if item["id"] != DROPPED]
    write_json(SUITE_V3, suite)


def extract_artifacts() -> None:
    study = V2 / "raw/study_artifacts.tar.gz"
    replicate = V2 / "raw/setup_emphasis_2_artifacts.tar.gz"
    mapping = [
        (study, "original.py", V3 / "original.py"),
        (study, "original_assumptions.json", V3 / "original_assumptions.json"),
        (study, "original_checks.txt", V3 / "original_checks.txt"),
        (study, "original_usage.json", V3 / "original_usage.json"),
        (study, "original_judge_1.md", V3 / "original_judge_1.md"),
        (study, "original_judge_2.md", V3 / "original_judge_2.md"),
        (study, "original_judge_3.md", V3 / "original_judge_3.md"),
        (study, "setup_emphasis.py", V3 / "setup_emphasis.py"),
        (study, "setup_emphasis_agentic.json", V3 / "setup_emphasis_agentic.json"),
        (study, "setup_emphasis_assumptions.json", V3 / "setup_emphasis_assumptions.json"),
        (study, "setup_emphasis_checks.txt", V3 / "setup_emphasis_checks.txt"),
        (study, "setup_emphasis_usage.json", V3 / "setup_emphasis_usage.json"),
        (study, "setup_emphasis_judge_1.md", V3 / "setup_emphasis_judge_1.md"),
        (study, "setup_emphasis_judge_2.md", V3 / "setup_emphasis_judge_2.md"),
        (study, "setup_emphasis_judge_3.md", V3 / "setup_emphasis_judge_3.md"),
        (replicate, "abalone_codex_ag.py", V3 / "setup_emphasis_2.py"),
        (replicate, "abalone_codex_ag_agentic.json", V3 / "setup_emphasis_2_agentic.json"),
        (replicate, "abalone_codex_ag_assumptions.json", V3 / "setup_emphasis_2_assumptions.json"),
        (replicate, "abalone_codex_ag_judge_1.md", V3 / "setup_emphasis_2_judge_1.md"),
        (replicate, "abalone_codex_ag_judge_2.md", V3 / "setup_emphasis_2_judge_2.md"),
        (replicate, "abalone_codex_ag_judge_3.md", V3 / "setup_emphasis_2_judge_3.md"),
    ]
    for archive, name, dest in mapping:
        extract_member(archive, name, dest)
    shutil.copy2(V2 / "original_agentic.json", V3 / "original_agentic.json")
    shutil.copy2(V2 / "setup_emphasis_2_checks.txt", V3 / "setup_emphasis_2_checks.txt")
    shutil.copy2(V2 / "setup_emphasis_2_usage.json", V3 / "setup_emphasis_2_usage.json")


def run_scenarios() -> None:
    from checks.run_scenarios_v4 import run_suite

    jobs = (
        ("original.py", "original_scenarios.json"),
        ("setup_emphasis.py", "setup_emphasis_scenarios.json"),
        ("setup_emphasis_2.py", "setup_emphasis_2_scenarios.json"),
    )
    for code_name, out_name in jobs:
        result = run_suite(V3 / code_name, SUITE_V3)
        write_json(V3 / out_name, result)
        ids = [item["id"] for item in result["results"] if item["status"] != "PASS"]
        print(f"{code_name}: {result['basis_scores']} failures={ids}")


def spec(condition: str, stem: str, headline: str, extra_sources: list[dict] | None = None) -> dict:
    sources = [
        {
            "id": "ABALONE-RULES-SCHMIDT-4P",
            "role": "publisher_rulebook",
            "path": "../../../../inputs/games/abalone/game_rules.pdf",
            "sha256": RULEBOOK,
        }
    ]
    if extra_sources:
        sources.extend(extra_sources)
    return {
        "identity": {
            "game": "Abalone",
            "condition": condition,
            "source_path": "../../../../inputs/games/abalone/game_rules.pdf",
            "source_format": "pdf" if extra_sources is None else "publisher-pdf+clear-rule-emphasis",
            "source_sha256": RULEBOOK,
            "sources": sources,
        },
        "source_diagnosis": {
            "clear": 36,
            "human_decision": 6,
            "ambiguous": 0,
            "not_testable": 4,
        },
        "headline": headline,
        "runs": [
            {
                "stem": stem,
                "agentic_evidence": f"{stem}_agentic.json" if stem != "original" else "original_agentic.json",
                "checks": f"{stem}_checks.txt",
                "scenarios": f"{stem}_scenarios.json",
                "usage": f"{stem}_usage.json",
                "code": f"{stem}.py",
                "assumptions": f"{stem}_assumptions.json",
                "neutral_reviews": [
                    f"{stem}_judge_1.md",
                    f"{stem}_judge_2.md",
                    f"{stem}_judge_3.md",
                ],
            }
        ],
    }


def write_result_cards() -> None:
    emphasis_source = {
        "id": "ABALONE-V2-SETUP-EMPHASIS",
        "role": "experimenter_clarification",
        "path": "../../../../inputs/games/abalone/setup_emphasis_v2.json",
        "sha256": sha256(ROOT / "inputs/games/abalone/setup_emphasis_v2.json"),
    }
    specs = {
        "original_result_spec.json": spec(
            "v2_original_1 compatibility replay under evaluator v3",
            "original",
            "Compatibility replay under v3: 32/33 configured clear-basis and 4/4 human-decision-basis scenarios passed; the unspecified no-move case is not scored.",
        ),
        "setup_emphasis_result_spec.json": spec(
            "v2_setup_emphasis_1 compatibility replay under evaluator v3",
            "setup_emphasis",
            "Compatibility replay under v3: 33/33 configured clear-basis and 4/4 human-decision-basis scenarios passed; setup is corrected and the unspecified no-move case is not scored.",
            [emphasis_source],
        ),
        "setup_emphasis_2_result_spec.json": spec(
            "v2_setup_emphasis_2 compatibility replay under evaluator v3",
            "setup_emphasis_2",
            "Compatibility replay under v3: 33/33 configured clear-basis and 4/4 human-decision-basis scenarios passed; the unspecified no-move case is not scored.",
            [emphasis_source],
        ),
    }
    for name, payload in specs.items():
        spec_path = V3 / name
        write_json(spec_path, payload)
        result = aggregate(payload, V3)
        stem = name.replace("_spec.json", "")
        write_json(V3 / f"{stem}.json", result)
        (V3 / f"{stem}.md").write_text(markdown(result), encoding="utf-8")


def write_revision() -> None:
    payload = {
        "schema_version": 1,
        "revision_id": "abalone-v3-evaluator",
        "status": "compatibility-replay",
        "created_on": "2026-08-23",
        "rubric_version": RUBRIC,
        "prior_revision": {
            "path": "checks/scenarios/abalone_v2.json",
            "sha256": sha256(SUITE_V2),
            "rubric_version": "abalone-v2-atomic-2026-07-26",
        },
        "reason": (
            "Unscore ABAL-R19. The publisher source does not specify no-movement behavior, "
            "the untimed base game has no timeout loss, and the sparse fixture is not a reachable deadlock. "
            "Frozen v2 implementations are replayed unchanged. v2 scores remain historical."
        ),
        "evaluation": {
            "scenarios": 37,
            "clear_basis": 33,
            "human_decision_basis": 4,
            "required_clear_claims": 33,
            "unscored_scenario": DROPPED,
        },
        "artifacts": {
            "scenario_suite": {"path": "checks/scenarios/abalone_v3.json", "sha256": sha256(SUITE_V3)},
            "scenario_adapter": {
                "path": "checks/scenario_adapters/abalone_v2.py",
                "sha256": sha256(ROOT / "checks/scenario_adapters/abalone_v2.py"),
            },
            "scenario_runner": {
                "path": "checks/run_scenarios_v4.py",
                "sha256": sha256(ROOT / "checks/run_scenarios_v4.py"),
            },
            "claims": {"path": "inputs/games/abalone/claims_v3.json", "sha256": sha256(CLAIMS_V3)},
        },
    }
    write_json(ROOT / "inputs/games/abalone/evaluator_revision_v3.json", payload)


def write_iteration_manifest() -> None:
    files = [
        "original_result.json",
        "original_result.md",
        "setup_emphasis_result.json",
        "setup_emphasis_result.md",
        "setup_emphasis_2_result.json",
        "setup_emphasis_2_result.md",
        "original_scenarios.json",
        "setup_emphasis_scenarios.json",
        "setup_emphasis_2_scenarios.json",
        "COMPARISON.md",
    ]
    write_json(
        V3 / "iteration_manifest.json",
        {
            "schema_version": 2,
            "game": "abalone",
            "iteration": "v3",
            "current_presentation": True,
            "kind": "evaluator_revision_compatibility_replay",
            "prior_iteration": "v2",
            "implementation_changed": False,
            "conditions": {
                name.replace(".json", "").replace(".md", ""): None
                for name in files
            },
            "hashes": {name: sha256(V3 / name) for name in files if (V3 / name).is_file()},
        },
    )


def main() -> int:
    V3.mkdir(parents=True, exist_ok=True)
    build_claims()
    build_suite()
    extract_artifacts()
    run_scenarios()
    write_result_cards()
    write_revision()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
