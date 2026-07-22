#!/usr/bin/env python3
"""Run the single-run clarified Bohnanza Base 2023 study sequentially."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import generation.run_bohnanza_source_experiment as legacy
from generation.codex_native import run_codex
from generation.pdf_pages import render_pdf_pages
from generation.run_expl import _agentic_gate, _event_commands

GAME_DIR = ROOT / "inputs/games/bohnanza_base_2023_clarified"
MANIFEST_PATH = GAME_DIR / "experiment_manifest.json"
RESULTS = ROOT / "results/scores/bohnanza_base_2023/clarified_1"
PROGRESS_PATH = RESULTS / "progress.json"
MODEL = "gpt-5.6-sol"
GENERATION_EFFORT = "low"
JUDGE_EFFORT = "medium"
GENERATION_PROMPT = (ROOT / "inputs/prompts/rulebook_to_python.txt").read_text(encoding="utf-8") + """

This packet also contains `profile_fixture_self_check.py`. Run it after `agentic_self_check.py`; it checks representation-only complete fixtures and contains no rule expectations.
"""


def source_manifest(sources: list[dict]) -> str:
    lines = ["# Assigned clarified source condition", ""]
    lines += [f"- `{source['packet_name']}` — `{source['role']}`" for source in sources]
    lines += [
        "",
        "`game_rules.pdf` is the publisher rulebook. `clarifications.json` is a user-approved experimenter clarification intervention, not publisher text; it is authoritative only for the four explicitly identified interpretations/transcriptions it contains.",
        "Use both assigned documents and no remembered, web, evaluator, or prior-run information. Surface any conflict rather than silently choosing.",
    ]
    return "\n".join(lines) + "\n"


def make_workspace(specification: dict) -> tuple[Path, list[Path]]:
    workspace = Path(tempfile.mkdtemp(prefix="boardbench_bohnanza_base_2023_"))
    sources = specification["sources"]
    for source in sources:
        shutil.copy2(GAME_DIR / source["path"], workspace / source["packet_name"])
    shutil.copy2(ROOT / "inputs/prompts/environment_contract.md", workspace / "ENVIRONMENT_CONTRACT.md")
    shutil.copy2(GAME_DIR / "environment_profile.json", workspace / "GAME_PROFILE.json")
    shutil.copy2(ROOT / "generation/agentic_self_check.py", workspace / "agentic_self_check.py")
    shutil.copy2(ROOT / "generation/profile_fixture_self_check.py", workspace / "profile_fixture_self_check.py")
    (workspace / "TASK.txt").write_text(GENERATION_PROMPT, encoding="utf-8")
    (workspace / "SOURCE_MANIFEST.md").write_text(source_manifest(sources), encoding="utf-8")
    rules = workspace / "game_rules.pdf"
    images = render_pdf_pages(rules, workspace / "game_rules_pages", dpi=150)
    return workspace, images


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["runs"] != ["clarified"]:
        raise RuntimeError("contract-v2 run order changed")
    for condition in manifest["conditions"].values():
        for source in condition["sources"]:
            path = GAME_DIR / source["path"]
            if not path.is_file() or sha256(path) != source["sha256"]:
                raise RuntimeError(f"source hash mismatch: {path}")
    for item in manifest["infrastructure"].values():
        path = ROOT / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise RuntimeError(f"infrastructure hash mismatch: {path}")
    return manifest


def state() -> dict:
    if PROGRESS_PATH.is_file():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {"schema_version": 1, "completed": [], "judged": [], "failed": [], "updated_at": None}


def save(value: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    value["updated_at"] = datetime.now(timezone.utc).isoformat()
    temporary = PROGRESS_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(PROGRESS_PATH)


def stem(condition: str) -> str:
    return "bohnanza_base_2023_clarified_codex_ag"


def run_dir(condition: str) -> Path:
    return RESULTS / "runs" / condition


def preserve(condition: str, workspace: Path, calls: list[dict], gate_output: str, manifest: dict) -> None:
    target = run_dir(condition)
    target.mkdir(parents=True, exist_ok=True)
    output_stem = stem(condition)
    copies = {
        "implementation.py": f"{output_stem}.py",
        "rule_coverage.md": f"{output_stem}_rule_coverage.md",
        "assumptions.json": f"{output_stem}_assumptions.json",
        "TASK.txt": f"{output_stem}_generation_prompt.md",
        "ENVIRONMENT_CONTRACT.md": f"{output_stem}_environment_contract.md",
        "GAME_PROFILE.json": f"{output_stem}_environment_profile.json",
        "SOURCE_MANIFEST.md": f"{output_stem}_source_manifest.md",
    }
    for source, destination in copies.items():
        shutil.copy2(workspace / source, target / destination)
    for attempt in range(len(calls)):
        for source, suffix in ((f"raw_response_{attempt}.md", ".md"), (f"events_{attempt}.jsonl", "_events.jsonl"), (f"usage_{attempt}.json", "_generation_usage.json")):
            shutil.copy2(workspace / source, target / f"{output_stem}_attempt_{attempt + 1}{suffix}")
    totals: dict[str, int] = {}
    for call in calls:
        for key, value in call.get("token_summary", {}).items():
            totals[key] = totals.get(key, 0) + int(value)
    (target / f"{output_stem}_usage.json").write_text(json.dumps({
        "call_count": len(calls),
        "elapsed_seconds_total": sum(float(call.get("elapsed_seconds", 0)) for call in calls),
        "token_totals": totals,
        "calls": calls,
        "actual_subscription_cost": None,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    evidence = {
        "protocol": "agentic-v3.1",
        "model": MODEL,
        "reasoning_effort": GENERATION_EFFORT,
        "verbosity": "low",
        "sandbox": "danger-full-access",
        "repair_count": len(calls) - 1,
        "agent_ran_self_check": any("agentic_self_check.py" in command for attempt in range(len(calls)) for command in _event_commands(workspace / f"events_{attempt}.jsonl")),
        "agent_ran_fixture_self_check": any("profile_fixture_self_check.py" in command for attempt in range(len(calls)) for command in _event_commands(workspace / f"events_{attempt}.jsonl")),
        "independent_gate_passed": True,
        "gate_output": gate_output,
        "implementation_sha256": sha256(workspace / "implementation.py"),
        "frozen_hashes": {key: value["sha256"] for key, value in manifest["infrastructure"].items()},
    }
    (target / f"{output_stem}_agentic_evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def evaluate(condition: str, manifest: dict) -> None:
    target, output_stem = run_dir(condition), stem(condition)
    code = target / f"{output_stem}.py"
    suite = ROOT / manifest["evaluation"]["suite"]
    groups = [
        ("TECHNICAL 01-04", [sys.executable, str(ROOT / "checks/run_checks.py"), "--game", output_stem, "--code-path", str(code), "--check", "01_result_file", "--check", "02_python_syntax", "--check", "03_startable_game", "--check", "04_required_api"]),
        ("ROBUSTNESS 05", [sys.executable, str(ROOT / "checks/run_checks.py"), "--game", output_stem, "--code-path", str(code), "--rollouts", "100", "--max-steps", "1000", "--seed", "1", "--check", "05_random_rollouts"]),
        ("INTERFACE 06", [sys.executable, str(ROOT / "checks/run_checks.py"), "--game", output_stem, "--code-path", str(code), "--check", "06_action_language"]),
        ("BASE CONTRACT-V2 SCENARIOS", [sys.executable, str(ROOT / "checks/run_scenarios.py"), "--code-path", str(code), "--scenarios", str(suite), "--json-output", str(target / f"{output_stem}_scenarios.json")]),
    ]
    sections = []
    for label, command in groups:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        sections.append(f"=== {label} ===\n$ {' '.join(command)}\nexit_code={result.returncode}\n{result.stdout}{result.stderr}")
        if label == "TECHNICAL 01-04" and result.returncode:
            raise RuntimeError(f"post-gate technical check failed:\n{result.stdout}{result.stderr}")
    (target / f"{output_stem}_checks.txt").write_text("\n\n".join(sections).rstrip() + "\n", encoding="utf-8")


def generate_one(condition: str, specification: dict, manifest: dict) -> None:
    workspace, images = make_workspace(specification)
    calls = []
    immutable = {
        "agentic_self_check.py": ROOT / "generation/agentic_self_check.py",
        "profile_fixture_self_check.py": ROOT / "generation/profile_fixture_self_check.py",
        "ENVIRONMENT_CONTRACT.md": ROOT / "inputs/prompts/environment_contract.md",
        "GAME_PROFILE.json": GAME_DIR / "environment_profile.json",
    }
    frozen = {name: sha256(workspace / name) for name in immutable}
    try:
        gate_output = "not run"
        for attempt in range(3):
            prompt = GENERATION_PROMPT if attempt == 0 else f"""Continue the same isolated implementation task. Repair only evaluator-neutral technical and canonical-contract failures using the gate output below. Use no outside game knowledge and do not modify either self-check, ENVIRONMENT_CONTRACT.md, or GAME_PROFILE.json. Re-run all three required validation commands.\n\n{gate_output}"""
            usage = run_codex(
                prompt=prompt,
                cwd=workspace,
                response_path=workspace / f"raw_response_{attempt}.md",
                events_path=workspace / f"events_{attempt}.jsonl",
                usage_path=workspace / f"usage_{attempt}.json",
                model=MODEL,
                effort=GENERATION_EFFORT,
                verbosity="low",
                mode="agentic",
                timeout=1800,
                image_paths=images,
                sandbox="danger-full-access",
            )
            calls.append(usage)
            legacy.audit_isolation(workspace / f"events_{attempt}.jsonl")
            changed = [name for name, digest in frozen.items() if not (workspace / name).is_file() or sha256(workspace / name) != digest]
            if changed:
                for name in changed:
                    shutil.copy2(immutable[name], workspace / name)
                passed, gate_output = False, f"agent modified immutable packet files: {', '.join(changed)}; originals restored"
            else:
                passed, gate_output = _agentic_gate(workspace, require_coverage=True, require_assumptions=True)
            if passed:
                fixture_check = subprocess.run([sys.executable, str(workspace / "profile_fixture_self_check.py")], cwd=workspace, text=True, capture_output=True)
                gate_output += "\n" + fixture_check.stdout + fixture_check.stderr
                passed = fixture_check.returncode == 0
            if passed:
                preserve(condition, workspace, calls, gate_output, manifest)
                evaluate(condition, manifest)
                return
        failure = run_dir(condition)
        failure.mkdir(parents=True, exist_ok=True)
        for path in workspace.iterdir():
            if path.is_file():
                shutil.copy2(path, failure / f"failed_{path.name}")
        raise RuntimeError(f"canonical gate failed after three attempts:\n{gate_output}")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def judge_one(condition: str) -> None:
    target, output_stem = run_dir(condition), stem(condition)
    workspace = Path(tempfile.mkdtemp(prefix="boardbench_v2_judge_"))
    try:
        rules = workspace / "game_rules.pdf"
        shutil.copy2(GAME_DIR / "game_rules.pdf", rules)
        shutil.copy2(GAME_DIR / "clarifications.json", workspace / "clarifications.json")
        shutil.copy2(GAME_DIR / "rulefacts.md", workspace / "approved_rulefacts.md")
        shutil.copy2(target / f"{output_stem}.py", workspace / "implementation.py")
        (workspace / "SOURCE_MANIFEST.md").write_text(source_manifest([
            {"packet_name": "game_rules.pdf", "role": "publisher_rulebook"},
            {"packet_name": "clarifications.json", "role": "experimenter_clarification"},
        ]), encoding="utf-8")
        images = render_pdf_pages(rules, workspace / "game_rules_pages", dpi=150)
        review = (ROOT / "inputs/prompts/llm_judge_review.md").read_text(encoding="utf-8")
        events = target / f"{output_stem}_judge_1_events.jsonl"
        run_codex(
            prompt=legacy.JUDGE_PREFIX + review,
            cwd=workspace,
            response_path=target / f"{output_stem}_judge_1.md",
            events_path=events,
            usage_path=target / f"{output_stem}_judge_1_usage.json",
            model=MODEL,
            effort=JUDGE_EFFORT,
            verbosity="low",
            mode="judge",
            timeout=1200,
            image_paths=images,
            sandbox="read-only",
        )
        legacy.audit_isolation(events)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_phase(phase: str, maximum: int | None) -> int:
    manifest, progress = load_manifest(), state()
    launched = 0
    key = "completed" if phase == "generate" else "judged"
    for condition in manifest["runs"]:
        if condition in progress[key] or (phase == "judge" and condition not in progress["completed"]):
            continue
        if maximum is not None and launched >= maximum:
            break
        try:
            if phase == "generate":
                generate_one(condition, manifest["conditions"][condition], manifest)
            else:
                judge_one(condition)
        except Exception as error:
            progress["failed"].append({"condition": condition, "phase": phase, "error": str(error)})
            save(progress)
            print(f"STOPPED {condition} {phase}: {error}", file=sys.stderr)
            return 1
        progress[key].append(condition)
        save(progress)
        launched += 1
        print(f"COMPLETED {condition} {phase}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("dry-run", "generate", "judge"), default="dry-run")
    parser.add_argument("--max-runs", type=int)
    args = parser.parse_args()
    manifest = load_manifest()
    if args.phase == "dry-run":
        print("\n".join(manifest["runs"]))
        return 0
    return run_phase(args.phase, args.max_runs)


if __name__ == "__main__":
    raise SystemExit(main())
