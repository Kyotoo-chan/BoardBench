#!/usr/bin/env python3
"""One-shot: rebuild bundled catan commits into per-backend workflow commits.

Run from repo root. Recovers artifacts from git history into ``.game_run_staging/``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import clear_run_artifacts  # noqa: E402
STAGING = REPO_ROOT / ".game_run_staging"
OUTPUTS = REPO_ROOT / "outputs"
BASE = "533a116"
# Dangling replay commits that still hold full catan artifacts after history rewrites.
CATAN_SOURCE_COMMITS = ("a8cec0e", "9a8bdf3", "64df722")

# kind: infra | prepare | generation | tests | plot (backend-level, both variants)
STEPS: list[dict] = [
    {"at": "2026-07-07T14:18:50+02:00", "msg": "fix notebook bootstrap cell and add run_pi_series", "kind": "infra"},
    {"at": "2026-07-07T14:30:15+02:00", "msg": "prepare catan rulebook and implementation brief", "kind": "prepare", "game": "catan"},
    {"at": "2026-07-07T14:38:22+02:00", "msg": "save catan claude oneshot and agentic generation", "kind": "generation", "game": "catan", "backend": "claude"},
    {"at": "2026-07-07T15:08:47+02:00", "msg": "save catan claude tests and gpt/codex judges", "kind": "tests", "game": "catan", "backend": "claude"},
    {"at": "2026-07-07T15:18:12+02:00", "msg": "pin catan plot after claude oneshot and agentic", "kind": "plot", "game": "catan", "backend": "claude"},
    {"at": "2026-07-07T15:26:19+02:00", "msg": "save catan codex oneshot and agentic generation", "kind": "generation", "game": "catan", "backend": "codex"},
    {"at": "2026-07-07T15:52:28+02:00", "msg": "save catan codex tests and gpt/codex judges", "kind": "tests", "game": "catan", "backend": "codex"},
    {"at": "2026-07-07T16:02:02+02:00", "msg": "pin catan plot after codex oneshot and agentic", "kind": "plot", "game": "catan", "backend": "codex"},
    {"at": "2026-07-07T16:10:55+02:00", "msg": "save catan pi oneshot and agentic generation", "kind": "generation", "game": "catan", "backend": "gpt"},
    {"at": "2026-07-07T16:48:33+02:00", "msg": "save catan pi tests and gpt/codex judges", "kind": "tests", "game": "catan", "backend": "gpt"},
    {"at": "2026-07-07T16:58:18+02:00", "msg": "pin catan plot after pi oneshot and agentic", "kind": "plot", "game": "catan", "backend": "gpt"},
]

VARIANTS = ("oneshot", "agentic")


def run(cmd: list[str], **kwargs) -> None:
    subprocess.run(cmd, cwd=REPO_ROOT, check=True, **kwargs)


def stage_outputs_snapshot() -> None:
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True)

    seen: set[str] = set()
    for commit in CATAN_SOURCE_COMMITS:
        listed = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit, "outputs/", "inputs/game_rules.pdf"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        for rel in listed.stdout.splitlines():
            if not rel or rel.endswith(".gitkeep"):
                continue
            name = Path(rel).name
            if name in seen:
                continue
            if not (name.startswith("cat_") or name.startswith("catan_") or rel.startswith("inputs/")):
                continue
            blob = subprocess.run(
                ["git", "show", f"{commit}:{rel}"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=True,
            )
            if rel.startswith("inputs/"):
                (STAGING / "_inputs_game_rules.pdf").write_bytes(blob.stdout)
            else:
                (STAGING / name).write_bytes(blob.stdout)
            seen.add(name)
    if not seen:
        raise RuntimeError("No catan artifacts found in CATAN_SOURCE_COMMITS")


def restore_run_files(game: str, backend: str, variant: str, *, include_tests: bool) -> None:
    from generation.config import output_stem

    impl = "gpt" if backend in {"pi", "gpt"} else backend
    stem = output_stem(game, impl, variant)
    names = [f"{stem}.py", f"{stem}.md"]
    if include_tests:
        names.append(f"{stem}_checks.txt")
        for judge in ("gpt", "codex"):
            names.append(f"{stem}_judge_{judge}.md")
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = STAGING / name
        if src.exists():
            shutil.copy2(src, OUTPUTS / name)


def restore_backend_files(game: str, backend: str, *, include_tests: bool) -> None:
    for variant in VARIANTS:
        restore_run_files(game, backend, variant, include_tests=include_tests)


def restore_prepare_files(game: str) -> None:
    rules = STAGING / "_inputs_game_rules.pdf"
    if rules.exists():
        shutil.copy2(rules, REPO_ROOT / "inputs" / "game_rules.pdf")
    brief = STAGING / f"{game}_implementation_brief.md"
    if brief.exists():
        shutil.copy2(brief, OUTPUTS / brief.name)


def clear_working_outputs() -> None:
    if not OUTPUTS.exists():
        OUTPUTS.mkdir(parents=True)
        return
    for path in OUTPUTS.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def reset_working_tree_for_replay() -> None:
    clear_working_outputs()
    for path in (REPO_ROOT / "plots").glob("cat_*"):
        if path.is_file():
            path.unlink()


def paths_for_step(step: dict) -> list[str]:
    from generation.game_run_workflow import generation_files, plot_files, test_files

    kind = step["kind"]
    game = step.get("game", "")
    backend = step.get("backend", "")
    if kind == "infra":
        return [
            "evaluation.ipynb",
            "evaluation2.ipynb",
            "generation/run_pi_series.py",
            "generation/run_codex_series.py",
            "generation/prepare_game_run.py",
            "docs/claude_generation_workflow.md",
            "generation/game_run_workflow.py",
            "generation/rebuild_catan_history.py",
            "plots/collect_scores.py",
            "plots/make_plots.py",
            ".cursor/skills/boardbench-game-run/SKILL.md",
            "AGENTS.md",
        ]
    if kind == "prepare":
        restore_prepare_files(game)
        return ["inputs/game_rules.pdf", f"outputs/{game}_implementation_brief.md"]
    if kind == "generation":
        clear_run_artifacts(game)
        restore_backend_files(game, backend, include_tests=False)
        return [p.relative_to(REPO_ROOT).as_posix() for p in generation_files(game, backend)]
    if kind == "tests":
        restore_backend_files(game, backend, include_tests=True)
        from generation.run_pilot_checks import refresh_run

        impl = "gpt" if backend in {"pi", "gpt"} else backend
        for variant in VARIANTS:
            refresh_run(game, impl, variant, rerun_base=False)
        return [p.relative_to(REPO_ROOT).as_posix() for p in test_files(game, backend)]
    if kind == "plot":
        run(
            [
                sys.executable,
                "generation/game_run_workflow.py",
                "plot",
                "--game",
                game,
                "--backend",
                backend,
            ]
        )
        return [p.relative_to(REPO_ROOT).as_posix() for p in plot_files(game)]
    raise ValueError(kind)


def commit_step(step: dict) -> None:
    paths = paths_for_step(step)
    env = {
        **dict(subprocess.os.environ),
        "GIT_AUTHOR_DATE": step["at"],
        "GIT_COMMITTER_DATE": step["at"],
    }
    existing = [path for path in paths if (REPO_ROOT / path).exists()]
    if not existing and step["kind"] != "plot":
        raise RuntimeError(f"No files for {step['msg']}: {paths}")
    if existing:
        run(["git", "add", *existing], env=env)
    if step["kind"] in {"plot", "generation"}:
        run(["git", "add", "-u", "outputs/"], env=env)
    run(["git", "commit", "-m", step["msg"]], env=env)


def main() -> int:
    stage_outputs_snapshot()
    run(["git", "reset", "--soft", BASE])
    run(["git", "reset", "HEAD"])
    reset_working_tree_for_replay()
    for step in STEPS:
        print(f"commit: {step['msg']}", flush=True)
        commit_step(step)
    if STAGING.exists():
        shutil.rmtree(STAGING)
    run(["git", "log", "--oneline", "-12"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
