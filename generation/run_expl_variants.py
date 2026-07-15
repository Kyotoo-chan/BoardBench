#!/usr/bin/env python3
"""Run isolated Exploding Kittens implementations through native Codex."""

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

MODEL = "gpt-5.6-sol"
GENERATION_EFFORT = "low"
JUDGE_EFFORT = "medium"
BASE_STEMS = ("expl_pdf", "expl_txt", "expl_anon", "expl_omit", "expl_error", "expl_vague")
STEMS = BASE_STEMS + tuple(f"{stem}_r2" for stem in BASE_STEMS) + ("expl_clarified_r1",)
SOURCE_FOR_STEM = {stem: stem.removesuffix("_r2") for stem in STEMS}
SOURCE_FOR_STEM["expl_clarified_r1"] = "expl_clarified"
PROTOCOLS = ("agentic-v2", "agentic-v2.1", "agentic-v2.2")
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
    for source_stem in sorted(set(SOURCE_FOR_STEM.values())):
        item = manifest["variants"][source_stem]
        path = REPO_ROOT / item["path"]
        if sha256(path) != item["sha256"]:
            raise RuntimeError(f"variant hash mismatch: {source_stem}")
        result[source_stem] = path
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


def implementation_prompt(source_name: str, protocol: str) -> str:
    prompt_name = {
        "agentic-v2": "rulebook_to_python_agentic_v2.txt",
        "agentic-v2.1": "rulebook_to_python.txt",
        "agentic-v2.2": "rulebook_to_python_agentic_v2_2.txt",
    }[protocol]
    task = (REPO_ROOT / "prompts" / prompt_name).read_text(encoding="utf-8")
    return f"""You are the sole implementation agent in an isolated BoardBench workspace.

Use only `{source_name}` and any attached rendered pages as game-rule evidence. Do not use remembered rules, web knowledge, repository files, evaluator tests, or assumptions from the game title. The interface contract below is not a rule source. If the supplied source is incomplete, contradictory, or vague, make the smallest explicit implementation assumption and list it in the response.

{INTERFACE_CONTRACT}

{task}
"""


def call_paths(stem: str, label: str) -> tuple[Path, Path, Path]:
    base = OUTPUTS / f"{stem}_{label}"
    return base.with_suffix(".md"), OUTPUTS / f"{stem}_{label}_events.jsonl", OUTPUTS / f"{stem}_{label}_usage.json"


def _event_commands(path: Path) -> list[str]:
    commands: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "command_execution" and isinstance(value.get("command"), str):
                commands.append(value["command"])
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            visit(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(dict.fromkeys(commands))


def _validate_assumptions(path: Path) -> str | None:
    if not path.is_file():
        return "assumptions.json is missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"assumptions.json is invalid: {exc}"
    if payload.get("version") != 1 or not isinstance(payload.get("assumptions"), list):
        return "assumptions.json needs version=1 and an assumptions list"
    required = {"id", "material", "source_location", "source_basis", "alternatives", "selected", "affected_mechanics"}
    for index, item in enumerate(payload["assumptions"]):
        if not isinstance(item, dict) or not required <= item.keys():
            return f"assumptions[{index}] is missing required fields"
        if item["material"] is not True or item["source_basis"] not in {"ambiguous", "missing", "contradictory"}:
            return f"assumptions[{index}] has invalid material/source_basis"
        if not isinstance(item["alternatives"], list) or len(item["alternatives"]) < 2:
            return f"assumptions[{index}] needs at least two alternatives"
        if not isinstance(item["affected_mechanics"], list) or not item["affected_mechanics"]:
            return f"assumptions[{index}] needs affected_mechanics"
    return None


def _agentic_gate(
    workspace: Path, *, require_coverage: bool, require_assumptions: bool = False
) -> tuple[bool, str]:
    implementation = workspace / "implementation.py"
    if not implementation.is_file() or not implementation.read_text(encoding="utf-8", errors="replace").strip():
        return False, "implementation.py is missing or empty"
    coverage = workspace / "rule_coverage.md"
    if require_coverage and (not coverage.is_file() or not coverage.read_text(encoding="utf-8", errors="replace").strip()):
        return False, "rule_coverage.md is missing or empty"
    if require_assumptions:
        error = _validate_assumptions(workspace / "assumptions.json")
        if error:
            return False, error
    sections = []
    passed = True
    for command in (
        [sys.executable, "-m", "py_compile", str(implementation)],
        [sys.executable, str(workspace / "agentic_self_check.py")],
    ):
        returncode, output, elapsed = run_command(command, cwd=workspace)
        sections.append(
            f"command={' '.join(command)}\nexit_code={returncode} elapsed_seconds={elapsed:.3f}\n{output.rstrip()}"
        )
        passed &= returncode == 0
    return passed, "\n\n".join(sections)


def run_implementation(stem: str, source: Path, protocol: str) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_{stem}_"))
    try:
        local_source = workspace / ("rulebook.pdf" if source.suffix.lower() == ".pdf" else "rulebook.txt")
        shutil.copy2(source, local_source)
        self_check = workspace / "agentic_self_check.py"
        shutil.copy2(REPO_ROOT / "generation" / "agentic_self_check.py", self_check)
        self_check_hash = sha256(self_check)
        images = render_pdf(local_source, workspace) if local_source.suffix == ".pdf" else []
        require_coverage = protocol in {"agentic-v2.1", "agentic-v2.2"}
        require_assumptions = protocol == "agentic-v2.2"
        prompt = implementation_prompt(local_source.name, protocol)
        (OUTPUTS / f"{stem}_generation_prompt.md").write_text(prompt, encoding="utf-8")

        all_commands: list[str] = []
        call_records: list[dict[str, object]] = []
        gate_ok = False
        gate_output = "not run"
        max_repairs = 2

        for attempt in range(max_repairs + 1):
            label = "generation" if attempt == 0 else f"repair_{attempt}"
            response_path = OUTPUTS / (f"{stem}.md" if attempt == 0 else f"{stem}_{label}.md")
            events_path = OUTPUTS / f"{stem}_{label}_events.jsonl"
            usage_path = OUTPUTS / f"{stem}_{label}_usage.json"
            artifact_instruction = " ".join(
                part for part in (
                    "Create or update `rule_coverage.md` by auditing every supplied rulebook section and named rule/card/combination against the code."
                    if require_coverage else "",
                    "Create or update schema-valid `assumptions.json` with only material source assumptions."
                    if require_assumptions else "",
                ) if part
            )
            call_prompt = prompt if attempt == 0 else f"""Continue the same isolated implementation task. Inspect and repair `implementation.py` using only the supplied rulebook and interface contract. Do not use outside game knowledge. Do not change `agentic_self_check.py`.

{INTERFACE_CONTRACT}

{artifact_instruction}

The evaluator-neutral independent gate reported:

```text
{gate_output}
```

Run both required commands yourself and keep repairing until they pass:

```text
python -m py_compile implementation.py
python agentic_self_check.py
```

Return only assumptions, files changed, and exact validation outcomes.
"""
            run_codex(
                prompt=call_prompt,
                cwd=workspace,
                response_path=response_path,
                events_path=events_path,
                usage_path=usage_path,
                model=MODEL,
                effort=GENERATION_EFFORT,
                mode="agentic",
                image_paths=images,
            )
            commands = _event_commands(events_path)
            all_commands.extend(commands)
            if not self_check.exists() or sha256(self_check) != self_check_hash:
                shutil.copy2(REPO_ROOT / "generation" / "agentic_self_check.py", self_check)
                gate_ok = False
                gate_output = "agent modified agentic_self_check.py; original restored"
            else:
                gate_ok, gate_output = _agentic_gate(
                    workspace,
                    require_coverage=require_coverage,
                    require_assumptions=require_assumptions,
                )
            ran_self_check = any("agentic_self_check.py" in command for command in all_commands)
            call_records.append(
                {
                    "attempt": attempt,
                    "label": label,
                    "commands": commands,
                    "independent_gate_passed": gate_ok,
                    "agent_ran_self_check": ran_self_check,
                }
            )
            if gate_ok and ran_self_check:
                break
        else:
            raise RuntimeError(f"{stem}: agentic implementation gate failed after {max_repairs} repairs\n{gate_output}")

        evidence = {
            "stem": stem,
            "protocol": protocol,
            "model": MODEL,
            "reasoning_effort": GENERATION_EFFORT,
            "implementation_file": "implementation.py",
            "rule_coverage_file": "rule_coverage.md" if require_coverage else None,
            "assumptions_file": "assumptions.json" if require_assumptions else None,
            "self_check_sha256": self_check_hash,
            "repair_count": len(call_records) - 1,
            "agent_ran_self_check": any("agentic_self_check.py" in command for command in all_commands),
            "independent_gate_passed": gate_ok,
            "commands": list(dict.fromkeys(all_commands)),
            "calls": call_records,
            "final_gate_output": gate_output,
        }
        (OUTPUTS / f"{stem}_agentic_evidence.json").write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        code_path = OUTPUTS / f"{stem}.py"
        shutil.copy2(workspace / "implementation.py", code_path)
        if require_coverage:
            shutil.copy2(workspace / "rule_coverage.md", OUTPUTS / f"{stem}_rule_coverage.md")
        if require_assumptions:
            shutil.copy2(workspace / "assumptions.json", OUTPUTS / f"{stem}_assumptions.json")
        return code_path
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_command(command: list[str], *, cwd: Path = REPO_ROOT) -> tuple[int, str, float]:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
            effort=JUDGE_EFFORT,
            mode="judge",
            image_paths=images,
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def aggregate_usage(stem: str) -> None:
    paths = (
        [OUTPUTS / f"{stem}_generation_usage.json"]
        + sorted(OUTPUTS.glob(f"{stem}_repair_*_usage.json"))
        + sorted(OUTPUTS.glob(f"{stem}_*_failed_*_usage.json"))
        + [OUTPUTS / f"{stem}_judge_{i}_usage.json" for i in range(1, 4)]
    )
    calls = [json.loads(path.read_text(encoding="utf-8")) for path in paths if path.exists()]
    token_totals: dict[str, int] = {}
    for call in calls:
        for key, value in call.get("token_summary", {}).items():
            token_totals[key] = token_totals.get(key, 0) + int(value)
    evidence_path = OUTPUTS / f"{stem}_agentic_evidence.json"
    protocol = json.loads(evidence_path.read_text(encoding="utf-8")).get("protocol") if evidence_path.exists() else None
    payload = {
        "stem": stem,
        "protocol": protocol,
        "model": MODEL,
        "generation_reasoning_effort": GENERATION_EFFORT,
        "judge_reasoning_effort": JUDGE_EFFORT,
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


def run_stem(stem: str, source: Path, protocol: str) -> None:
    # Each experiment is committed before the next starts. Git retains the
    # complete artifact set while the working tree contains only the current run.
    clear_outputs()
    print(f"[{stem}] implementation", flush=True)
    code_path = run_implementation(stem, source, protocol)
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
    parser.add_argument("--protocol", choices=PROTOCOLS, default="agentic-v2.2")
    args = parser.parse_args()

    WORKSPACES.mkdir(exist_ok=True)
    sources = variant_paths()
    run_stem(args.stem, sources[SOURCE_FOR_STEM[args.stem]], args.protocol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
