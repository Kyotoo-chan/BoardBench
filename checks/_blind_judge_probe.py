#!/usr/bin/env python3
"""One-off blind judge probe: anonymized mismatch packet, no game-name leaks."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_CHECKS = Path(__file__).resolve().parent
for p in (REPO_ROOT, _CHECKS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from judge_packet import compose_judge_prompt, read_rules_text  # noqa: E402
from generation.llm_cli import build_llm_command, ensure_direct_llm_response, run_llm_subprocess  # noqa: E402

SCORE_RE = re.compile(r"(?im)^\s*score\s*:\s*([01](?:\.\d+)?)\s*$")
TIMEOUT = 900
GAMES = REPO_ROOT / "inputs" / "games"


@dataclass(frozen=True)
class BlindScenario:
    name: str
    code_git: str
    rules_path: Path
    code_replacements: tuple[tuple[str, str], ...]
    rules_replacements: tuple[tuple[str, str], ...]


SCENARIOS: dict[str, BlindScenario] = {
    "ek_vs_mjh": BlindScenario(
        name="ek_vs_mjh",
        code_git="70a0834:outputs/expl_codex_os.py",
        rules_path=GAMES / "mahjong" / "game_rules.pdf",
        code_replacements=(
            (r"(?i)exploding\s*kitten", "card_type_alpha"),
            (r"(?i)exploding_kitten", "card_type_alpha"),
            (r"(?i)kitten", "card_type"),
            (r"(?i)katze(?:n)?", "card"),
            (r"(?i)zombiekatze", "special_card_a"),
            (r"(?i)Exploding Kittens", "Card Game A"),
            (r"(?i)BoardBench", "Benchmark"),
        ),
        rules_replacements=(
            (r"(?i)mah[\-\s]?jongg?", "Tile Game B"),
            (r"(?i)Mah-Jongg", "Tile Game B"),
            (r"(?i)BoardBench", "Benchmark"),
        ),
    ),
    "hav_vs_aba": BlindScenario(
        name="hav_vs_aba",
        code_git="ea83cfd:outputs/havannah_oneshot.py",
        rules_path=GAMES / "abalone" / "game_rules.pdf",
        code_replacements=(
            (r"(?i)havannah", "Board Game A"),
            (r"(?i)BoardBench", "Benchmark"),
        ),
        rules_replacements=(
            (r"(?i)abalone", "Board Game B"),
            (r"(?i)BoardBench", "Benchmark"),
        ),
    ),
}


def git_show(rev_path: str) -> str:
    r = subprocess.run(
        ["git", "show", rev_path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or f"git show failed: {rev_path}")
    return r.stdout


def anonymize(text: str, pairs: tuple[tuple[str, str], ...]) -> str:
    out = text
    for pattern, repl in pairs:
        out = re.sub(pattern, repl, out)
    return out


def build_blind_packet(code: str, rules: str) -> str:
    return "\n\n".join(
        [
            "# Implementation review packet",
            "- review type: rulebook vs generated Python environment",
            "- note: artifacts are anonymized; judge only the provided content",
            "",
            "## Judge prompt",
            compose_judge_prompt(),
            "",
            "## Rule text",
            rules,
            "",
            "## Generated implementation",
            "```python\n" + code + "\n```",
        ]
    )


def parse_score(text: str) -> float | None:
    matches = SCORE_RE.findall(text)
    if not matches:
        return None
    score = float(matches[-1])
    return score if 0.0 <= score <= 1.0 else None


def run_judge(backend: str, scenario: BlindScenario) -> tuple[str, float | None, float, Path]:
    code = anonymize(git_show(scenario.code_git), scenario.code_replacements)
    rules = anonymize(read_rules_text(scenario.rules_path), scenario.rules_replacements)
    if not rules.strip():
        raise RuntimeError("rulebook has no extractable text")

    packet = build_blind_packet(code, rules)
    out_path = REPO_ROOT / "outputs" / f"judge_blind_{scenario.name}_{backend}.md"

    models = {
        "pi": ("openai-codex/gpt-5.5:xhigh", "xhigh"),
        "codex": ("gpt-5.4", "xhigh"),
    }
    model, effort = models[backend]
    cmd = build_llm_command(backend, model, effort, mode="judge")

    started = time.perf_counter()
    result = run_llm_subprocess(cmd, prompt_text=packet, cwd=REPO_ROOT, timeout=TIMEOUT)
    text = ensure_direct_llm_response(result, step=f"blind judge {scenario.name}/{backend}")
    elapsed = time.perf_counter() - started
    out_path.write_text(text, encoding="utf-8")
    return backend, parse_score(text), elapsed, out_path


def main() -> int:
    scenario_name = "ek_vs_mjh"
    backend = "pi"
    args = sys.argv[1:]
    for arg in args:
        if arg in SCENARIOS:
            scenario_name = arg
        elif arg in {"pi", "codex"}:
            backend = arg
        else:
            print(f"FAIL unknown arg {arg!r}; use scenario {sorted(SCENARIOS)} and backend pi|codex", flush=True)
            return 1

    scenario = SCENARIOS[scenario_name]
    try:
        b, score, elapsed, path = run_judge(backend, scenario)
        if score is None:
            print(f"FAIL {scenario.name}/{b}  no score  {elapsed:.0f}s  -> {path.name}", flush=True)
            return 1
        print(f"OK   {scenario.name}/{b}  score={score:.3f}  {elapsed:.0f}s  -> {path.name}", flush=True)
        return 0
    except Exception as exc:
        print(f"FAIL {scenario.name}/{backend}  {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
