"""Shared helpers for BoardBench checks.
Why: keeps import, rollout, path, and result-reporting code out of tiny check files.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


DISPLAY_NAME_WIDTH = 22
UNITS_WIDTH = 15
ELAPSED_FIELD_WIDTH = 7

SMOKE_CHECK_PREFIXES = frozenset({"01", "02", "03", "04"})
SMOKE_CHECK_WEIGHT = 1
QUALITY_CHECK_WEIGHT = 10

DEFAULT_ROLLOUTS = 100

CHECK_LINE_RE = re.compile(
    r"^(?P<status>OK|FAIL)\s+"
    r"(?P<name>\S+)\s+"
    r"(?P<passed>\d+)/(?P<total>\d+)\s+"
    r"score=(?P<score>[0-9.]+)\s+"
    r"(?P<elapsed>[0-9.]+)s"
    r"(?:\s+(?P<message>.*))?$"
)
SUMMARY_LINE_RE = re.compile(
    r"^----\s+summary\s+"
    r"(?P<checks_passed>\d+)/(?P<checks_total>\d+)\s+"
    r"score=(?P<score>[0-9.]+)\s+"
    r"(?P<elapsed>[0-9.]+)s\s*$"
)


REQUIRED_GAME_METHODS = [
    "initial_state",
    "current_player",
    "legal_actions",
    "apply_action",
    "is_terminal",
    "returns",
    "render",
    "action_to_name",
    "name_to_action",
]


@dataclass(frozen=True)
class CheckResult:
    passed: int
    total: int
    message: str | None = None

    @property
    def score(self) -> float:
        """Normalized 0..1 score for this check.

        Checks report passed/total units. The score makes every check directly
        comparable while preserving the detailed unit counts.
        """

        if self.total <= 0:
            return 0.0
        return max(0.0, min(1.0, self.passed / self.total))


@dataclass(frozen=True)
class CheckContext:
    repo_root: Path
    game: str
    code_path: Path
    rollouts: int
    max_steps: int
    seed: int
    judge_path: Path | None = None


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_code_path(raw_path: str | Path, repo_root: Path) -> Path:
    requested = Path(raw_path)
    if requested.is_absolute():
        return requested

    candidates = [Path.cwd() / requested, repo_root / requested]
    if requested.parts and requested.parts[0] != "code":
        candidates.append(repo_root / "code" / requested)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return candidates[0].resolve()


def resolve_optional_path(raw_path: str | Path | None, repo_root: Path) -> Path | None:
    if raw_path is None:
        return None
    requested = Path(raw_path)
    if requested.is_absolute():
        return requested
    for candidate in [Path.cwd() / requested, repo_root / requested]:
        if candidate.exists():
            return candidate.resolve()
    return (repo_root / requested).resolve()


def import_generated_module(ctx: CheckContext) -> ModuleType:
    module_name = f"boardbench_generated_{ctx.code_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, ctx.code_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {ctx.code_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    with suppress_generated_output():
        spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def suppress_generated_output():
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        yield


def make_game(ctx: CheckContext) -> tuple[ModuleType, Any, Any]:
    module = import_generated_module(ctx)
    game_cls = getattr(module, "Game")
    with suppress_generated_output():
        game = game_cls()
        state = game.initial_state()
    return module, game, state


def apply_action(game: Any, state: Any, action: Any) -> Any:
    with suppress_generated_output():
        next_state = game.apply_action(state, action)
    return state if next_state is None else next_state


def legal_actions(game: Any, state: Any) -> list[Any]:
    with suppress_generated_output():
        return list(game.legal_actions(state))


def current_player(game: Any, state: Any) -> int:
    with suppress_generated_output():
        return int(game.current_player(state))


def is_terminal(game: Any, state: Any) -> bool:
    with suppress_generated_output():
        return bool(game.is_terminal(state))


def returns(game: Any, state: Any) -> list[float]:
    with suppress_generated_output():
        return list(game.returns(state))


def validate_state_basics(game: Any, state: Any, actions: list[Any]) -> str | None:
    with suppress_generated_output():
        rendered = game.render(state)
        if rendered != game.render(state):
            return "render(state) is not deterministic"

    names: set[str] = set()
    for action in actions:
        with suppress_generated_output():
            name = game.action_to_name(action)
            roundtrip = game.name_to_action(name)
        if name in names:
            return f"duplicate action name {name!r}"
        names.add(name)
        if roundtrip != action:
            return f"action name did not round-trip: {name!r}"
    return None


def random_rollout(game: Any, state: Any, rng: random.Random, max_steps: int) -> str | None:
    for _step in range(max_steps):
        terminal = is_terminal(game, state)
        actions = legal_actions(game, state)
        message = validate_state_basics(game, state, actions)
        if message:
            return message

        if terminal:
            if actions:
                return "terminal state still has legal actions"
            return None

        if not actions:
            return "non-terminal state has no legal actions"

        state = apply_action(game, state, rng.choice(actions))

    # The smoke test is about crashes/invalid states. Hitting the step cap is
    # allowed so long as every sampled state and action was usable.
    return None


def check_weight(check_name: str) -> int:
    """Smoke checks 01-04 weigh less; all later checks weigh equally."""

    prefix = check_name.split("_", 1)[0]
    if prefix in SMOKE_CHECK_PREFIXES:
        return SMOKE_CHECK_WEIGHT
    return QUALITY_CHECK_WEIGHT


def format_check_line(
    status: str,
    name: str,
    units: str,
    score: float,
    elapsed: float,
    message: str | None = None,
    *,
    name_width: int | None = None,
) -> str:
    width = name_width if name_width is not None else max(DISPLAY_NAME_WIDTH, len("summary"), len(name))
    line = (
        f"{status:<4} {name:<{width}} {units:>{UNITS_WIDTH}} "
        f"score={score:.3f} {elapsed:>{ELAPSED_FIELD_WIDTH}.2f}s"
    )
    if message:
        line += f"  {message}"
    return line


def format_summary_line(
    checks_passed: int,
    checks_total: int,
    score: float,
    elapsed: float,
    *,
    name_width: int | None = None,
) -> str:
    return format_check_line(
        "----",
        "summary",
        f"{checks_passed}/{checks_total}",
        score,
        elapsed,
        name_width=name_width,
    )


@dataclass(frozen=True)
class ParsedCheckLine:
    status: str
    name: str
    passed: int
    total: int
    score: float
    elapsed: float
    message: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "OK"

    @property
    def weight(self) -> int:
        return check_weight(self.name)


def parse_check_lines(text: str) -> list[ParsedCheckLine]:
    parsed: list[ParsedCheckLine] = []
    for line in text.splitlines():
        match = CHECK_LINE_RE.match(line)
        if match is None:
            continue
        groups = match.groupdict()
        parsed.append(
            ParsedCheckLine(
                status=groups["status"],
                name=groups["name"],
                passed=int(groups["passed"]),
                total=int(groups["total"]),
                score=float(groups["score"]),
                elapsed=float(groups["elapsed"]),
                message=groups.get("message") or None,
            )
        )
    return parsed


def weighted_score_from_checks(checks: list[ParsedCheckLine]) -> float:
    if not checks:
        return 0.0
    weighted_sum = sum(check.weight * check.score for check in checks)
    total_weight = sum(check.weight for check in checks)
    return weighted_sum / total_weight if total_weight else 0.0


def summarize_check_lines(checks: list[ParsedCheckLine]) -> dict[str, int | float]:
    checks_passed = sum(1 for check in checks if check.ok)
    checks_total = len(checks)
    weight_total = sum(check.weight for check in checks)
    weighted_score_sum = sum(check.weight * check.score for check in checks)
    return {
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "units_passed": sum(check.passed for check in checks),
        "units_total": sum(check.total for check in checks),
        "score": weighted_score_from_checks(checks),
        "seconds": sum(check.elapsed for check in checks),
        "weight_total": weight_total,
        "weighted_score_sum": weighted_score_sum,
    }


def parse_check_output_text(text: str) -> dict[str, int | float]:
    checks = parse_check_lines(text)
    if checks:
        return summarize_check_lines(checks)

    match = SUMMARY_LINE_RE.search(text)
    if match is None:
        return {
            "checks_passed": 0,
            "checks_total": 0,
            "units_passed": 0,
            "units_total": 0,
            "score": 0.0,
            "seconds": 0.0,
            "weight_total": 0,
            "weighted_score_sum": 0.0,
        }

    checks_passed = int(match.group("checks_passed"))
    checks_total = int(match.group("checks_total"))
    score = float(match.group("score"))
    seconds = float(match.group("elapsed"))
    weight_total = checks_total * QUALITY_CHECK_WEIGHT
    return {
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "units_passed": checks_passed,
        "units_total": checks_total,
        "score": score,
        "seconds": seconds,
        "weight_total": weight_total,
        "weighted_score_sum": score * weight_total,
    }


def aggregate_phase_stats(phase_stats: list[dict[str, int | float]]) -> dict[str, int | float]:
    if not phase_stats:
        return {
            "checks_passed": 0,
            "checks_total": 0,
            "units_passed": 0,
            "units_total": 0,
            "score": 0.0,
            "seconds": 0.0,
            "weight_total": 0,
            "weighted_score_sum": 0.0,
        }

    weight_total = sum(int(stats["weight_total"]) for stats in phase_stats)
    weighted_score_sum = sum(float(stats["weighted_score_sum"]) for stats in phase_stats)
    return {
        "checks_passed": sum(int(stats["checks_passed"]) for stats in phase_stats),
        "checks_total": sum(int(stats["checks_total"]) for stats in phase_stats),
        "units_passed": sum(int(stats["units_passed"]) for stats in phase_stats),
        "units_total": sum(int(stats["units_total"]) for stats in phase_stats),
        "score": (weighted_score_sum / weight_total) if weight_total else 0.0,
        "seconds": sum(float(stats["seconds"]) for stats in phase_stats),
        "weight_total": weight_total,
        "weighted_score_sum": weighted_score_sum,
    }


def add_elapsed_to_result_output(output: str, extra_elapsed: float) -> str:
    if extra_elapsed <= 0:
        return output

    lines: list[str] = []
    adjusted = False
    for line in output.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = CHECK_LINE_RE.match(body)
        if match is not None and not adjusted:
            groups = match.groupdict()
            elapsed = float(groups["elapsed"]) + extra_elapsed
            body = format_check_line(
                groups["status"],
                groups["name"],
                f"{groups['passed']}/{groups['total']}",
                float(groups["score"]),
                elapsed,
                groups.get("message") or None,
            )
            adjusted = True
        lines.append(body + newline)
    return "".join(lines)
