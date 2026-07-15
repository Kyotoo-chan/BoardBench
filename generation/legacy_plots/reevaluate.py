#!/usr/bin/env python3
"""Re-evaluate the six frozen implementations with the current evaluator."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.codex_native import run_codex
from generation.run_expl_variants import JUDGE_EFFORT, MODEL, judge_prompt, render_pdf

OUT_DIR = REPO_ROOT / "results" / "scores" / "exploding_kittens" / "variants" / "evaluation_v2"
WORKSPACES = REPO_ROOT / "generation_workspaces"
EXPERIMENTS = [
    (1, "expl_pdf", "Original PDF"),
    (2, "expl_txt", "Faithful TXT"),
    (3, "expl_anon", "Anonymized"),
    (4, "expl_omit", "Omissions"),
    (5, "expl_error", "False rules"),
    (6, "expl_vague", "Vague rules"),
]
RUBRIC_FILES = [
    "inputs/games/expl/game_rules.pdf",
    "inputs/games/expl/rulefacts.md",
    "checks/scenarios/expl.json",
    "checks/scenario_adapters/expl.py",
    "checks/run_scenarios.py",
    "prompts/llm_judge_review.md",
]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8", errors="replace")


def experiment_commit(number: int) -> str:
    prefix = f"experiment {number:02d}:"
    matches = [
        line.split("\t", 1)[0]
        for line in git("log", "--format=%H%x09%s").splitlines()
        if line.split("\t", 1)[1].startswith(prefix)
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one commit for {prefix}, found {len(matches)}")
    return matches[0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def extract_code(commit: str, stem: str, target: Path) -> None:
    target.write_text(git("show", f"{commit}:outputs/{stem}.py"), encoding="utf-8")


def run_checks(commit: str, stem: str, code_path: Path) -> None:
    python = sys.executable
    scenario_json = OUT_DIR / f"{stem}_scenarios.json"
    groups = [
        ("technical gate 01-04", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "01_result_file", "--check", "02_python_syntax", "--check", "03_startable_game", "--check", "04_required_api"]),
        ("runtime robustness 05", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "05_random_rollouts", "--rollouts", "100", "--max-steps", "1000", "--seed", "1"]),
        ("interface 06", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "06_action_language", "--max-steps", "1000", "--seed", "1"]),
        ("canonical cited scenarios v2", [python, "checks/run_scenarios.py", "--code-path", str(code_path), "--scenarios", "checks/scenarios/expl.json", "--json-output", str(scenario_json)]),
    ]
    sections = [f"experiment_commit={commit}", "evaluator_version=2"]
    for label, command in groups:
        returncode, output = run_command(command)
        sections.append(f"=== {label} ===\nexit_code={returncode}\n{output.rstrip()}")
    (OUT_DIR / f"{stem}_checks.txt").write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def run_judge(commit: str, stem: str, index: int) -> None:
    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_v2_{stem}_judge{index}_", dir=WORKSPACES))
    try:
        pdf = workspace / "canonical_rulebook.pdf"
        facts = workspace / "canonical_rulefacts.md"
        code = workspace / "implementation.py"
        shutil.copy2(REPO_ROOT / "inputs/games/expl/game_rules.pdf", pdf)
        shutil.copy2(REPO_ROOT / "inputs/games/expl/rulefacts.md", facts)
        extract_code(commit, stem, code)
        images = render_pdf(pdf, workspace)
        run_codex(
            prompt=judge_prompt(),
            cwd=workspace,
            response_path=OUT_DIR / f"{stem}_judge_{index}.md",
            events_path=OUT_DIR / f"{stem}_judge_{index}_events.jsonl",
            usage_path=OUT_DIR / f"{stem}_judge_{index}_usage.json",
            model=MODEL,
            effort=JUDGE_EFFORT,
            mode="judge",
            image_paths=images,
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def save_manifest(commits: dict[str, str], judges: bool) -> None:
    payload = {
        "evaluation_version": 2,
        "status": "posthoc_after_evaluator_correction",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "implementations_unchanged": True,
        "judges_rerun": judges,
        "judge_model": MODEL if judges else None,
        "judge_reasoning_effort": JUDGE_EFFORT if judges else None,
        "experiment_commits": commits,
        "rubric_files": {path: sha256(REPO_ROOT / path) for path in RUBRIC_FILES},
        "note": "Post-hoc evaluator development; preserve v1 results and do not describe v2 as preregistered evidence.",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judges", action="store_true", help="Run three corrected fresh judges per frozen implementation")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACES.mkdir(exist_ok=True)
    commits = {stem: experiment_commit(number) for number, stem, _ in EXPERIMENTS}
    with tempfile.TemporaryDirectory(prefix="boardbench_v2_") as temp:
        temp_dir = Path(temp)
        for _, stem, _ in EXPERIMENTS:
            print(f"[{stem}] checks", flush=True)
            code_path = temp_dir / f"{stem}.py"
            extract_code(commits[stem], stem, code_path)
            run_checks(commits[stem], stem, code_path)
            if args.judges:
                print(f"[{stem}] judges [1, 2, 3]", flush=True)
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [executor.submit(run_judge, commits[stem], stem, index) for index in range(1, 4)]
                    for future in concurrent.futures.as_completed(futures):
                        future.result()
    judges_present = all(
        (OUT_DIR / f"{stem}_judge_{index}.md").exists()
        for _, stem, _ in EXPERIMENTS
        for index in range(1, 4)
    )
    save_manifest(commits, judges_present)
    print(f"wrote evaluator-v2 artifacts to {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
