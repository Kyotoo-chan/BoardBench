#!/usr/bin/env python3
"""Run the preregistered Bohnanza source experiment strictly sequentially."""

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
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generation.codex_native import run_codex
from generation.pdf_pages import render_pdf_pages
from generation.run_expl import _agentic_gate, _event_commands

GAME_DIR = ROOT / "inputs" / "games" / "bohnanza"
MANIFEST_PATH = GAME_DIR / "experiment_manifest.json"
OUTPUTS = ROOT / "outputs"
PROGRESS_PATH = ROOT / "results" / "scores" / "bohnanza" / "source_experiment" / "progress.json"
SELF_CHECK = ROOT / "generation" / "agentic_self_check.py"
TASK_SOURCE = ROOT / "inputs" / "prompts" / "rulebook_to_python.txt"
SCENARIOS = ROOT / "checks" / "scenarios" / "bohnanza.json"
MODEL = "gpt-5.6-sol"
GENERATION_EFFORT = "low"
JUDGE_EFFORT = "medium"

GENERATION_PROMPT = """You are the sole implementation agent in an isolated BoardBench workspace.

Read `SOURCE_MANIFEST.md` and `IMPLEMENTATION_TASK.txt` completely, then inspect every supplied source and all attached fresh PDF page images. Implement the complete assigned 4-5-player source condition.

Use only files in this workspace as game-rule evidence. Do not use remembered rules, web knowledge, benchmark scenarios, evaluator facts, prior implementations, or assumptions from the game title.

Create the actual files `implementation.py`, `rule_coverage.md`, and schema-valid `assumptions.json`. Audit every supplied section and named bean/rule into coverage. Run exactly:

python -m py_compile implementation.py
python agentic_self_check.py

Repair every failure. Do not modify `agentic_self_check.py`.
"""

JUDGE_PREFIX = """You are one of three fresh, mutually blind neutral BoardBench reviewers. Work only with SOURCE_MANIFEST.md, the labelled canonical sources, approved_rulefacts.md, attached fresh PDF page images, and implementation.py in this isolated packet. Do not inspect checks, scenarios, scores, prior reviews, other implementations, repository files, or outside game knowledge. Preserve the difference between publisher rules, user observations, and human decisions. Unsupported concerns are questions, not penalties.

"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for condition in manifest["conditions"].values():
        for source in condition["sources"]:
            path = GAME_DIR / source["path"]
            if not path.is_file() or sha256(path) != source["sha256"]:
                raise RuntimeError(f"source hash mismatch: {path}")
    expected = [f"{condition}_{repeat}" for repeat in range(1, 4)
                for condition in ("pdf_only", "json_clean", "json_mutated", "pdf_mutated")]
    if manifest["sequential_order"] != expected:
        raise RuntimeError("manifest order must be round-robin and sequential")
    return manifest


def progress() -> dict[str, Any]:
    if PROGRESS_PATH.is_file():
        return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    return {"schema_version": 1, "completed": [], "judged": [], "failed": [], "updated_at": None}


def save_progress(value: dict[str, Any]) -> None:
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    value["updated_at"] = datetime.now(timezone.utc).isoformat()
    temporary = PROGRESS_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(PROGRESS_PATH)


def stem(run_id: str) -> str:
    return f"bohnanza_src_{run_id}_ag"


def source_manifest(sources: list[dict[str, str]]) -> str:
    lines = ["# Assigned source condition", ""]
    for source in sources:
        lines.append(f"- `{source['packet_name']}` — `{source['role']}`")
    lines += [
        "",
        "The publisher rulebook governs gameplay. A user-observation component file may establish observed component identities, counts, and printed Bohnometer values, but must not silently override gameplay. Record material conflicts in assumptions.json.",
        "Use no remembered or web rules.",
    ]
    return "\n".join(lines) + "\n"


def make_workspace(condition: dict[str, Any]) -> tuple[Path, list[Path]]:
    workspace = Path(tempfile.mkdtemp(prefix="boardbench_source_packet_"))
    images: list[Path] = []
    sources = condition["sources"]
    for source in sources:
        destination = workspace / source["packet_name"]
        shutil.copy2(GAME_DIR / source["path"], destination)
        if destination.suffix.lower() == ".pdf":
            images += render_pdf_pages(destination, workspace / f"{destination.stem}_pages", dpi=150)
    shutil.copy2(SELF_CHECK, workspace / "agentic_self_check.py")
    shutil.copy2(TASK_SOURCE, workspace / "IMPLEMENTATION_TASK.txt")
    (workspace / "SOURCE_MANIFEST.md").write_text(source_manifest(sources), encoding="utf-8")
    (workspace / "TASK.txt").write_text(GENERATION_PROMPT, encoding="utf-8")
    return workspace, images


def preserve_generation(run_id: str, workspace: Path, usage: dict[str, Any], gate_output: str) -> None:
    output_stem = stem(run_id)
    copies = {
        "implementation.py": f"{output_stem}.py",
        "rule_coverage.md": f"{output_stem}_rule_coverage.md",
        "assumptions.json": f"{output_stem}_assumptions.json",
        "raw_response.md": f"{output_stem}.md",
        "events.jsonl": f"{output_stem}_events.jsonl",
        "generation_usage.json": f"{output_stem}_generation_usage.json",
        "TASK.txt": f"{output_stem}_generation_prompt.md",
    }
    for source, destination in copies.items():
        shutil.copy2(workspace / source, OUTPUTS / destination)
    evidence = {
        "protocol": "agentic-v2.2",
        "model": usage["model"],
        "reasoning_effort": usage["reasoning_effort"],
        "verbosity": usage["verbosity"],
        "sandbox": usage.get("sandbox"),
        "repair_count": 0,
        "agent_ran_self_check": any("agentic_self_check.py" in command for command in _event_commands(workspace / "events.jsonl")),
        "independent_gate_passed": True,
        "self_check_sha256": sha256(SELF_CHECK),
        "implementation_sha256": sha256(workspace / "implementation.py"),
        "gate_output": gate_output,
    }
    (OUTPUTS / f"{output_stem}_agentic_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def run_local_evaluation(run_id: str) -> None:
    output_stem = stem(run_id)
    code = OUTPUTS / f"{output_stem}.py"
    groups = [
        ("TECHNICAL 01-04", [sys.executable, str(ROOT / "checks/run_checks.py"), "--game", output_stem, "--code-path", str(code), "--check", "01_result_file", "--check", "02_python_syntax", "--check", "03_startable_game", "--check", "04_required_api"]),
        ("ROBUSTNESS 05", [sys.executable, str(ROOT / "checks/run_checks.py"), "--game", output_stem, "--code-path", str(code), "--rollouts", "100", "--max-steps", "1000", "--seed", "1", "--check", "05_random_rollouts"]),
        ("INTERFACE 06", [sys.executable, str(ROOT / "checks/run_checks.py"), "--game", output_stem, "--code-path", str(code), "--check", "06_action_language"]),
        ("RULE FIDELITY SCENARIOS", [sys.executable, str(ROOT / "checks/run_scenarios.py"), "--code-path", str(code), "--scenarios", str(SCENARIOS), "--json-output", str(OUTPUTS / f"{output_stem}_scenarios.json")]),
    ]
    sections = []
    for label, command in groups:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        sections.append(f"=== {label} ===\n$ {' '.join(command)}\nexit_code={result.returncode}\n{result.stdout}{result.stderr}")
    (OUTPUTS / f"{output_stem}_checks.txt").write_text("\n\n".join(sections).rstrip() + "\n", encoding="utf-8")


def quota_error(error: Exception) -> bool:
    text = str(error).casefold()
    return any(fragment in text for fragment in ("usage limit", "weekly limit", "rate limit", "quota", "too many requests"))


def generate_one(run_id: str, condition: dict[str, Any]) -> None:
    workspace, images = make_workspace(condition)
    try:
        usage = run_codex(
            prompt=GENERATION_PROMPT,
            cwd=workspace,
            response_path=workspace / "raw_response.md",
            events_path=workspace / "events.jsonl",
            usage_path=workspace / "generation_usage.json",
            model=MODEL,
            effort=GENERATION_EFFORT,
            verbosity="low",
            mode="agentic",
            timeout=1200,
            image_paths=images,
            sandbox="workspace-write",
        )
        passed, gate_output = _agentic_gate(workspace, require_coverage=True, require_assumptions=True)
        if not passed:
            raise RuntimeError(f"independent gate failed:\n{gate_output}")
        preserve_generation(run_id, workspace, usage, gate_output)
        run_local_evaluation(run_id)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def judge_one(run_id: str, index: int) -> None:
    output_stem = stem(run_id)
    workspace = Path(tempfile.mkdtemp(prefix="boardbench_judge_packet_"))
    try:
        rules = workspace / "game_rules.pdf"
        components = workspace / "game_components.json"
        shutil.copy2(GAME_DIR / "game_rules.pdf", rules)
        shutil.copy2(GAME_DIR / "game_components.json", components)
        shutil.copy2(GAME_DIR / "rulefacts.md", workspace / "approved_rulefacts.md")
        shutil.copy2(OUTPUTS / f"{output_stem}.py", workspace / "implementation.py")
        (workspace / "SOURCE_MANIFEST.md").write_text(source_manifest([
            {"packet_name": "game_rules.pdf", "role": "publisher_rulebook"},
            {"packet_name": "game_components.json", "role": "user_observation"},
        ]), encoding="utf-8")
        images = render_pdf_pages(rules, workspace / "game_rules_pages", dpi=150)
        review = (ROOT / "inputs/prompts/llm_judge_review.md").read_text(encoding="utf-8")
        run_codex(
            prompt=JUDGE_PREFIX + review,
            cwd=workspace,
            response_path=OUTPUTS / f"{output_stem}_judge_{index}.md",
            events_path=OUTPUTS / f"{output_stem}_judge_{index}_events.jsonl",
            usage_path=OUTPUTS / f"{output_stem}_judge_{index}_usage.json",
            model=MODEL,
            effort=JUDGE_EFFORT,
            verbosity="low",
            mode="judge",
            timeout=1200,
            image_paths=images,
            sandbox="read-only",
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_judges(manifest: dict[str, Any], maximum: int | None) -> int:
    state = progress()
    completed = set(state.get("completed", []))
    judged = set(state.get("judged", []))
    launched = 0
    for run_id in manifest["sequential_order"]:
        if run_id not in completed:
            continue
        for index in (1, 2, 3):
            judge_id = f"{run_id}_judge_{index}"
            if judge_id in judged:
                continue
            if maximum is not None and launched >= maximum:
                return 0
            try:
                judge_one(run_id, index)
            except Exception as error:
                state["failed"].append({"run": judge_id, "error": str(error), "quota_like": quota_error(error)})
                save_progress(state)
                print(f"STOPPED {judge_id}: {error}", file=sys.stderr)
                return 75 if quota_error(error) else 1
            state.setdefault("judged", []).append(judge_id)
            save_progress(state)
            judged.add(judge_id)
            launched += 1
            print(f"COMPLETED {judge_id}", flush=True)
    return 0


def generate(manifest: dict[str, Any], maximum: int | None) -> int:
    state = progress()
    completed = set(state["completed"])
    launched = 0
    for run_id in manifest["sequential_order"]:
        if run_id in completed:
            continue
        if maximum is not None and launched >= maximum:
            break
        condition_name = run_id.rsplit("_", 1)[0]
        try:
            generate_one(run_id, manifest["conditions"][condition_name])
        except Exception as error:
            state["failed"].append({"run": run_id, "error": str(error), "quota_like": quota_error(error)})
            save_progress(state)
            print(f"STOPPED {run_id}: {error}", file=sys.stderr)
            return 75 if quota_error(error) else 1
        state["completed"].append(run_id)
        save_progress(state)
        completed.add(run_id)
        launched += 1
        print(f"COMPLETED {run_id}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("dry-run", "generate", "judges"), default="dry-run")
    parser.add_argument("--max-runs", type=int, help="optional sequential launch cap for this invocation")
    args = parser.parse_args()
    manifest = load_manifest()
    if args.phase == "dry-run":
        print("\n".join(manifest["sequential_order"]))
        return 0
    if args.phase == "judges":
        return run_judges(manifest, args.max_runs)
    return generate(manifest, args.max_runs)


if __name__ == "__main__":
    raise SystemExit(main())
