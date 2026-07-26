#!/usr/bin/env python3
"""Generate one versioned BoardBench implementation with a fail-closed packet."""

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

from generation.clean_outputs import OUTPUTS, entries
from generation.codex_native import run_codex
from generation.pdf_pages import render_pdf_pages
from generation.source_condition import (
    validate_packet_files,
    validate_packet_sources,
    validate_pair,
    validate_pdf_renders,
    validate_sources,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(path: str | Path) -> Path:
    value = Path(path)
    return value.resolve() if value.is_absolute() else (ROOT / value).resolve()


def load_config(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    required = {"game", "run_id", "condition_kind", "source_base_dir", "sources", "profile", "profile_fixture_self_check"}
    missing = required - value.keys()
    if value.get("schema_version") != 1 or missing:
        raise ValueError(f"invalid hardened run config; missing={sorted(missing)}")
    if value["condition_kind"] == "clarified" and not {"original_run_config", "original_evidence"} <= value.keys():
        raise ValueError("clarified run config needs original_run_config and original_evidence")
    return value


def config_digest(config: dict) -> str:
    return hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def require_committed(path: Path) -> None:
    try:
        relative = path.resolve().relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise ValueError(f"paired artifact must be inside the repository: {path}") from exc
    exists = subprocess.run(["git", "cat-file", "-e", f"HEAD:{relative}"], cwd=ROOT, capture_output=True)
    changed = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", relative], cwd=ROOT)
    if exists.returncode or changed.returncode:
        raise ValueError(f"paired artifact must be committed and unchanged: {relative}")


def original_pair(config: dict, *, require_frozen: bool = True) -> tuple[dict, dict] | tuple[None, None]:
    if config["condition_kind"] != "clarified":
        return None, None
    config_path = resolve(config["original_run_config"])
    evidence_path = resolve(config["original_evidence"])
    if require_frozen:
        require_committed(config_path)
        require_committed(evidence_path)
    value = load_config(config_path)
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if value["condition_kind"] != "original" or value["game"] != config["game"]:
        raise ValueError("clarified run must reference the matching original config")
    if not evidence.get("success") or evidence.get("condition_kind") != "original" or evidence.get("game") != config["game"]:
        raise ValueError("clarified run needs successful matching original evidence")
    if evidence.get("run_config_sha256") != config_digest(value):
        raise ValueError("original evidence does not match original run config")
    defaults = {
        "model": "gpt-5.6-sol", "effort": "low", "verbosity": "low",
        "max_repairs": 2, "timeout": 1800,
    }
    for key, default in defaults.items():
        if value.get(key, default) != config.get(key, default):
            raise ValueError(f"clarified run changed paired setting: {key}")
    for key, default in (
        ("profile", None),
        ("profile_fixture_self_check", None),
        ("prompt", "inputs/prompts/rulebook_to_python.txt"),
        ("contract", "inputs/prompts/environment_contract_v2.md"),
    ):
        original_path = resolve(value.get(key, default))
        clarified_path = resolve(config.get(key, default))
        if sha256(original_path) != sha256(clarified_path):
            raise ValueError(f"clarified run changed paired artifact: {key}")
    return value, evidence


def source_manifest(config: dict) -> str:
    return json.dumps({
        "condition_kind": config["condition_kind"],
        "sources": config["sources"],
    }, indent=2, ensure_ascii=False) + "\n"


def build_workspace(config: dict) -> tuple[Path, list[Path], set[str], dict[str, str], dict[str, dict]]:
    source_base = resolve(config["source_base_dir"])
    sources = config["sources"]
    if config["condition_kind"] == "clarified":
        original, _evidence = original_pair(config)
        validate_pair(
            original["sources"], sources,
            resolve(original["source_base_dir"]), source_base,
        )
    else:
        validate_sources("original", sources, source_base)

    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_{config['game']}_{config['run_id']}_"))
    images: list[Path] = []
    for source in sources:
        destination = workspace / source["packet_name"]
        shutil.copy2(source_base / source["path"], destination)
        if destination.suffix.lower() == ".pdf":
            images += render_pdf_pages(destination, workspace / f"{destination.stem}_pages", dpi=150)

    infrastructure = {
        "ENVIRONMENT_CONTRACT.md": resolve(config.get("contract", "inputs/prompts/environment_contract_v2.md")),
        "GAME_PROFILE.json": resolve(config["profile"]),
        "agentic_self_check.py": ROOT / "generation/agentic_self_check.py",
        "profile_fixture_self_check.py": resolve(config["profile_fixture_self_check"]),
    }
    for name, source in infrastructure.items():
        shutil.copy2(source, workspace / name)
    prompt_path = resolve(config.get("prompt", "inputs/prompts/rulebook_to_python.txt"))
    prompt = prompt_path.read_text(encoding="utf-8")
    (workspace / "TASK.txt").write_text(prompt, encoding="utf-8")
    (workspace / "SOURCE_MANIFEST.json").write_text(source_manifest(config), encoding="utf-8")

    allowed = {path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()}
    immutable = validate_packet_files(workspace, allowed)
    validate_packet_sources(immutable, sources)
    validate_pdf_renders(workspace, sources, images)
    render_evidence = {
        path.relative_to(workspace).as_posix(): json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(workspace.rglob("render_manifest.json"))
    }
    return workspace, images, allowed, immutable, render_evidence


def validate_assumptions(path: Path) -> str | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"invalid assumptions.json: {exc}"
    if value.get("version") != 1 or not isinstance(value.get("assumptions"), list):
        return "assumptions.json needs version=1 and assumptions list"
    required = {"id", "material", "source_location", "source_basis", "alternatives", "selected", "affected_mechanics"}
    for index, item in enumerate(value["assumptions"]):
        if not isinstance(item, dict) or not required <= item.keys():
            return f"assumptions[{index}] is missing required fields"
        if item["material"] is not True or item["source_basis"] not in {"ambiguous", "missing", "conflicting"}:
            return f"assumptions[{index}] has invalid material/source_basis"
        if not isinstance(item["id"], str) or not item["id"].strip() or not isinstance(item["source_location"], str) or not item["source_location"].strip():
            return f"assumptions[{index}] has invalid ID/source_location"
        if (
            not isinstance(item["alternatives"], list)
            or len(item["alternatives"]) < 2
            or any(not isinstance(value, str) or not value.strip() for value in item["alternatives"])
        ):
            return f"assumptions[{index}] needs at least two non-empty string alternatives"
        if not isinstance(item["selected"], str) or item["selected"] not in item["alternatives"]:
            return f"assumptions[{index}] selected value is not an alternative"
        if (
            not isinstance(item["affected_mechanics"], list)
            or not item["affected_mechanics"]
            or any(not isinstance(value, str) or not value.strip() for value in item["affected_mechanics"])
        ):
            return f"assumptions[{index}] needs non-empty string affected_mechanics"
    return None


def gate(workspace: Path) -> tuple[bool, str]:
    required = ("implementation.py", "rule_coverage.md", "assumptions.json")
    missing = [name for name in required if not (workspace / name).is_file()]
    if missing:
        return False, f"missing required artifacts: {', '.join(missing)}"
    assumptions_error = validate_assumptions(workspace / "assumptions.json")
    if assumptions_error:
        return False, assumptions_error
    commands = (
        [sys.executable, "-m", "py_compile", "implementation.py"],
        [sys.executable, "agentic_self_check.py"],
        [sys.executable, "profile_fixture_self_check.py"],
        [
            sys.executable, str(ROOT / "checks/check_player_counts.py"),
            "--code-path", "implementation.py", "--profile", "GAME_PROFILE.json",
        ],
    )
    sections, passed = [], True
    for command in commands:
        result = subprocess.run(command, cwd=workspace, text=True, capture_output=True)
        sections.append(f"$ {' '.join(command)}\nexit_code={result.returncode}\n{result.stdout}{result.stderr}".rstrip())
        passed &= result.returncode == 0
    return passed, "\n\n".join(sections)


def preserve(
    config: dict,
    workspace: Path,
    host: Path,
    calls: list[dict],
    checks: list[str],
    success: bool,
    render_evidence: dict[str, dict],
    original_evidence_sha256: str | None,
) -> None:
    outputs = OUTPUTS
    outputs.mkdir(exist_ok=True)
    stem = config.get("output_stem", f"{config['game']}_codex_ag")
    copies = {
        "implementation.py": f"{stem}.py",
        "assumptions.json": f"{stem}_assumptions.json",
        "rule_coverage.md": f"{stem}_rule_coverage.md",
        "TASK.txt": f"{stem}_task.txt",
    }
    for source, destination in copies.items():
        if (workspace / source).is_file():
            shutil.copy2(workspace / source, outputs / destination)
    responses = []
    event_lines = []
    for index in range(len(calls)):
        response = host / f"response_{index}.md"
        events = host / f"events_{index}.jsonl"
        if response.is_file():
            responses.append(f"# Attempt {index + 1}\n\n{response.read_text(encoding='utf-8')}")
        if events.is_file():
            event_lines += events.read_text(encoding="utf-8").splitlines()
    (outputs / f"{stem}.md").write_text("\n\n".join(responses).rstrip() + "\n", encoding="utf-8")
    (outputs / f"{stem}_events.jsonl").write_text("\n".join(event_lines).rstrip() + "\n", encoding="utf-8")
    (outputs / f"{stem}_checks.txt").write_text("\n\n".join(checks).rstrip() + "\n", encoding="utf-8")
    evidence = {
        "schema_version": 1,
        "protocol": "hardened-iteration-v1",
        "game": config["game"],
        "run_id": config["run_id"],
        "condition_kind": config["condition_kind"],
        "model": config.get("model", "gpt-5.6-sol"),
        "reasoning_effort": config.get("effort", "low"),
        "success": success,
        "repair_count": max(0, len(calls) - 1),
        "calls": calls,
        "source_manifest": config["sources"],
        "run_config_sha256": config_digest(config),
        "original_evidence_sha256": original_evidence_sha256,
        "render_manifests": render_evidence,
        "implementation_sha256": sha256(workspace / "implementation.py") if (workspace / "implementation.py").is_file() else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (outputs / f"{stem}_agentic.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(config: dict) -> bool:
    remaining = entries(OUTPUTS)
    if remaining:
        raise RuntimeError("outputs must be empty before generation: " + ", ".join(path.name for path in remaining))
    workspace, images, initial_allowed, immutable, render_evidence = build_workspace(config)
    host = Path(tempfile.mkdtemp(prefix="boardbench_host_artifacts_"))
    calls: list[dict] = []
    checks: list[str] = []
    source_base = resolve(config["source_base_dir"])
    original, original_evidence = original_pair(config)
    original_evidence_sha256 = sha256(resolve(config["original_evidence"])) if original_evidence else None
    try:
        for attempt in range(int(config.get("max_repairs", 2)) + 1):
            allowed = initial_allowed | {
                name for name in ("implementation.py", "rule_coverage.md", "assumptions.json")
                if (workspace / name).is_file()
            }
            feedback = checks[-1] if checks else ""
            prompt = (workspace / "TASK.txt").read_text(encoding="utf-8") if attempt == 0 else (
                "Continue the same isolated task. Repair only evaluator-neutral technical, artifact, and public-contract failures. "
                "Do not modify packet files and do not use outside game knowledge.\n\n" + feedback
            )
            call = run_codex(
                prompt=prompt,
                cwd=workspace,
                response_path=host / f"response_{attempt}.md",
                events_path=host / f"events_{attempt}.jsonl",
                usage_path=host / f"usage_{attempt}.json",
                model=config.get("model", "gpt-5.6-sol"),
                effort=config.get("effort", "low"),
                verbosity=config.get("verbosity", "low"),
                mode="agentic",
                timeout=int(config.get("timeout", 1800)),
                image_paths=images,
                packet_files=allowed,
                source_kind=config["condition_kind"],
                sources=config["sources"],
                source_base_dir=source_base,
                original_sources=original["sources"] if original else None,
                original_source_base_dir=resolve(original["source_base_dir"]) if original else None,
            )
            calls.append(call)
            changed = [name for name, digest in immutable.items() if not (workspace / name).is_file() or sha256(workspace / name) != digest]
            if changed:
                checks.append(f"attempt {attempt + 1}: immutable packet changed: {', '.join(changed)}")
                break
            passed, output = gate(workspace)
            checks.append(f"attempt {attempt + 1}:\n{output}")
            if passed:
                preserve(config, workspace, host, calls, checks, True, render_evidence, original_evidence_sha256)
                return True
        preserve(config, workspace, host, calls, checks, False, render_evidence, original_evidence_sha256)
        return False
    except Exception as exc:
        checks.append(f"launch failure: {exc.__class__.__name__}: {exc}")
        preserve(config, workspace, host, calls, checks, False, render_evidence, original_evidence_sha256)
        raise
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
        shutil.rmtree(host, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    return 0 if run(load_config(args.config)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
