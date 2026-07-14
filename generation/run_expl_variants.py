#!/usr/bin/env python3
"""Run the frozen six-variant Exploding Kittens experiment through native Codex."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.codex_native import run_codex
from generation.llm_cli import extract_code_block

MODEL = "gpt-5.6-sol"
EFFORT = "medium"
STEMS = ("expl_pdf", "expl_txt", "expl_anon", "expl_omit", "expl_error", "expl_vague")
CANONICAL_HASH = "f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853"
OUTPUTS = REPO_ROOT / "outputs"
WORKSPACES = REPO_ROOT / "generation_workspaces"
MANIFEST_PATH = REPO_ROOT / "inputs" / "games" / "expl" / "variants" / "manifest.json"

INTERFACE_CONTRACT = """# BoardBench public interface contract

This is evaluator-neutral infrastructure, not an additional source of game rules.

- Implement one self-contained standard-library Python module.
- `Game()` defaults to two players and player 0 starts; optional `num_players` and seed parameters are welcome.
- Nonterminal returns are zero for every player. Terminal returns are +1 for the winner and -1 for each loser.
- Provide `GameState` and `Game` with initial_state, current_player, legal_actions, apply_action, is_terminal, returns, render, action_to_name, and name_to_action.
- Terminal states have no legal actions.
- Every legal action must round-trip through a unique, stable, human-readable name. Preserve the supplied source's card/effect labels in action names instead of inventing or translating synonyms.
- Choices required by the source (targets, donated/requested cards, positions, reactions) must be explicit states/actions rather than silently chosen.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variant_paths() -> dict[str, Path]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["canonical_sha256"] != CANONICAL_HASH:
        raise RuntimeError("variant manifest canonical hash changed")
    result: dict[str, Path] = {}
    for stem in STEMS:
        item = manifest["variants"][stem]
        path = REPO_ROOT / item["path"]
        if sha256(path) != item["sha256"]:
            raise RuntimeError(f"variant hash mismatch: {stem}")
        result[stem] = path
    return result


def render_pdf(pdf: Path, target_dir: Path) -> list[Path]:
    prefix = target_dir / "page"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "150", str(pdf), str(prefix)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return sorted(target_dir.glob("page-*.png"))


def implementation_prompt(source_name: str) -> str:
    task = (REPO_ROOT / "prompts" / "rulebook_to_python.txt").read_text(encoding="utf-8")
    return f"""You are the sole implementation agent in an isolated BoardBench workspace.

Use only `{source_name}` and any attached rendered pages as game-rule evidence. Do not use remembered rules, web knowledge, repository files, evaluator tests, or assumptions from the game title. The interface contract below is not a rule source. If the supplied source is incomplete, contradictory, or vague, make the smallest explicit implementation assumption and list it in the response.

{INTERFACE_CONTRACT}

{task}
"""


def call_paths(stem: str, label: str) -> tuple[Path, Path, Path]:
    base = OUTPUTS / f"{stem}_{label}"
    return base.with_suffix(".md"), OUTPUTS / f"{stem}_{label}_events.jsonl", OUTPUTS / f"{stem}_{label}_usage.json"


def run_implementation(stem: str, source: Path) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_{stem}_", dir=WORKSPACES))
    try:
        local_source = workspace / ("rulebook.pdf" if source.suffix.lower() == ".pdf" else "rulebook.txt")
        shutil.copy2(source, local_source)
        images = render_pdf(local_source, workspace) if local_source.suffix == ".pdf" else []
        prompt_path = workspace / "prompt.md"
        prompt_path.write_text(implementation_prompt(local_source.name), encoding="utf-8")

        response_path = OUTPUTS / f"{stem}.md"
        events_path = OUTPUTS / f"{stem}_generation_events.jsonl"
        usage_path = OUTPUTS / f"{stem}_generation_usage.json"
        run_codex(
            prompt=prompt_path.read_text(encoding="utf-8"),
            cwd=workspace,
            response_path=response_path,
            events_path=events_path,
            usage_path=usage_path,
            model=MODEL,
            effort=EFFORT,
            mode="agentic",
            image_paths=images,
        )

        response = response_path.read_text(encoding="utf-8")
        code = extract_code_block(response)
        if code is None:
            candidates = sorted(workspace.glob("*.py"))
            if len(candidates) != 1:
                raise RuntimeError(f"{stem}: no unique Python module in response/workspace")
            code = candidates[0].read_text(encoding="utf-8")
        code_path = OUTPUTS / f"{stem}.py"
        code_path.write_text(code, encoding="utf-8")
        return code_path
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_command(command: list[str]) -> tuple[int, str, float]:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "") + (result.stderr or ""), time.perf_counter() - started


def run_checks(stem: str, code_path: Path) -> None:
    python = sys.executable
    groups = [
        (
            "technical gate 01-04",
            [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "01_result_file", "--check", "02_python_syntax", "--check", "03_startable_game", "--check", "04_required_api"],
        ),
        ("runtime robustness 05", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "05_random_rollouts", "--rollouts", "100", "--max-steps", "1000", "--seed", "1"]),
        ("interface 06", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "06_action_language", "--max-steps", "1000", "--seed", "1"]),
        ("canonical cited scenarios", [python, "checks/run_scenarios.py", "--code-path", str(code_path), "--scenarios", "checks/scenarios/expl.json", "--json-output", str(OUTPUTS / f"{stem}_scenarios.json")]),
    ]
    sections: list[str] = []
    for label, command in groups:
        returncode, output, elapsed = run_command(command)
        sections.append(f"=== {label} ===\nexit_code={returncode} elapsed_seconds={elapsed:.3f}\n{output.rstrip()}\n")
    (OUTPUTS / f"{stem}_checks.txt").write_text("\n".join(sections), encoding="utf-8")


def judge_prompt() -> str:
    review = (REPO_ROOT / "prompts" / "llm_judge_review.md").read_text(encoding="utf-8")
    return f"""You are one of three fresh, mutually blind rule reviewers. Work only with canonical_rulebook.pdf, attached canonical page images, canonical_rulefacts.md, and implementation.py in this isolated packet. Do not use outside game knowledge. Do not inspect check logs, other reviews, other variants, repository files, or filenames as evidence. The canonical PDF and approved facts are the evaluation reference even if the implementation was generated from a degraded source variant.

{review}
"""


def run_one_judge(stem: str, code_path: Path, index: int) -> None:
    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_{stem}_judge{index}_", dir=WORKSPACES))
    try:
        pdf = workspace / "canonical_rulebook.pdf"
        facts = workspace / "canonical_rulefacts.md"
        code = workspace / "implementation.py"
        shutil.copy2(REPO_ROOT / "inputs" / "games" / "expl" / "game_rules.pdf", pdf)
        shutil.copy2(REPO_ROOT / "inputs" / "games" / "expl" / "rulefacts.md", facts)
        shutil.copy2(code_path, code)
        images = render_pdf(pdf, workspace)
        prompt = judge_prompt()
        response, events, usage = call_paths(stem, f"judge_{index}")
        run_codex(
            prompt=prompt,
            cwd=workspace,
            response_path=response,
            events_path=events,
            usage_path=usage,
            model=MODEL,
            effort=EFFORT,
            mode="judge",
            image_paths=images,
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def aggregate_usage(stem: str) -> None:
    paths = [OUTPUTS / f"{stem}_generation_usage.json"] + [OUTPUTS / f"{stem}_judge_{i}_usage.json" for i in range(1, 4)]
    calls = [json.loads(path.read_text(encoding="utf-8")) for path in paths if path.exists()]
    token_totals: dict[str, int] = {}
    for call in calls:
        for key, value in call.get("token_summary", {}).items():
            token_totals[key] = token_totals.get(key, 0) + int(value)
    payload = {
        "stem": stem,
        "model": MODEL,
        "reasoning_effort": EFFORT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "call_count": len(calls),
        "token_totals": token_totals,
        "elapsed_seconds_total": round(sum(float(call.get("elapsed_seconds", 0)) for call in calls), 3),
        "calls": calls,
        "actual_subscription_cost": None,
        "cost_note": "Codex OAuth subscription calls expose tokens/quota but no trustworthy per-call monetary charge.",
    }
    (OUTPUTS / f"{stem}_usage.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clear_outputs() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    for path in OUTPUTS.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def run_stem(stem: str, source: Path) -> None:
    # Each experiment is committed before the next starts. Git retains the
    # complete artifact set while the working tree contains only the current run.
    clear_outputs()
    print(f"[{stem}] implementation", flush=True)
    code_path = run_implementation(stem, source)
    print(f"[{stem}] grouped checks", flush=True)
    run_checks(stem, code_path)

    print(f"[{stem}] judges [1, 2, 3]", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_one_judge, stem, code_path, index) for index in range(1, 4)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    aggregate_usage(stem)
    print(f"[{stem}] complete", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stem", choices=STEMS, required=True)
    args = parser.parse_args()

    WORKSPACES.mkdir(exist_ok=True)
    sources = variant_paths()
    run_stem(args.stem, sources[args.stem])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
