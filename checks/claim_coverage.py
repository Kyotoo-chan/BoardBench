"""Validate atomic rule-claim coverage for scenario suites."""

from __future__ import annotations

import json
from pathlib import Path

CLASSIFICATIONS = {"clear", "ambiguous", "missing", "conflicting", "untestable"}
EXPECTATION_KEYS = {
    "current_player", "terminal", "legal_action_count", "legal_action_count_min",
    "legal_action_name_contains_any", "legal_action_name_not_contains_any",
    "legal_action_name_contains_all_groups", "legal_action_name_not_contains_all_groups",
    "legal_action_delta", "returns", "returns_sorted", "previous_action_legal", "adapter",
}
ACTION_KEYS = {
    "adapter", "name", "normalized", "contains_any", "contains_all", "contains_all_groups",
    "prefer_contains_all_groups", "select", "index",
}


def _check_expectation_keys(expected: object, label: str, *, search: bool = False) -> bool:
    if not isinstance(expected, dict):
        raise ValueError(f"{label} expectation must be an object")
    allowed = EXPECTATION_KEYS | ({"current_player_relation"} if search else set())
    unknown = set(expected) - allowed
    if unknown:
        raise ValueError(f"{label} has unsupported expectation keys: {sorted(unknown)}")
    return bool(expected)


def load_claim_inventory(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    claims = value.get("claims")
    if value.get("version") != 1 or not isinstance(claims, list) or not claims:
        raise ValueError("claim inventory needs version=1 and a non-empty claims list")
    ids = [claim.get("id") for claim in claims]
    if any(not claim_id for claim_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("claim IDs must be non-empty and unique")
    for claim in claims:
        if claim.get("classification") not in CLASSIFICATIONS:
            raise ValueError(f"invalid claim classification: {claim.get('id')}")
        if not isinstance(claim.get("material"), bool) or not isinstance(claim.get("testable"), bool):
            raise ValueError(f"claim needs boolean material/testable: {claim.get('id')}")
        if claim["classification"] == "untestable" and claim["testable"]:
            raise ValueError(f"untestable claim cannot be testable: {claim.get('id')}")
    return value


def validate_claim_coverage(inventory_path: Path, scenarios: list[dict]) -> dict:
    inventory = load_claim_inventory(inventory_path)
    claims = {claim["id"]: claim for claim in inventory["claims"]}
    mapped: dict[str, list[str]] = {claim_id: [] for claim_id in claims}
    for scenario in scenarios:
        initial_check = _check_expectation_keys(scenario.get("initial", {}), f"scenario {scenario.get('id')} initial")
        step_check = False
        for index, step in enumerate(scenario.get("steps", []), 1):
            action = step.get("action", {})
            if not isinstance(action, dict) or set(action) - ACTION_KEYS:
                raise ValueError(f"scenario {scenario.get('id')} step {index} has unsupported action selector")
            expectation = _check_expectation_keys(step.get("expect", {}), f"scenario {scenario.get('id')} step {index}")
            step_check |= bool(action) or expectation
        search_check = bool(scenario.get("search"))
        if search_check:
            _check_expectation_keys(scenario.get("expect", {}), f"scenario {scenario.get('id')} search", search=True)
        terminal_check = bool(scenario.get("terminal_rollout"))
        if terminal_check:
            _check_expectation_keys(scenario.get("expect", {}), f"scenario {scenario.get('id')} terminal")
        checkable = initial_check or step_check or search_check or terminal_check
        if not checkable:
            raise ValueError(f"scenario {scenario.get('id')} has no checkable expectation, action, or search")
        for claim_id in scenario.get("fact_ids", []):
            if claim_id not in claims:
                raise ValueError(f"scenario {scenario.get('id')} references unknown claim {claim_id}")
            mapped[claim_id].append(str(scenario.get("id")))
            classification = claims[claim_id]["classification"]
            if scenario.get("basis") == "clear" and classification != "clear":
                raise ValueError(f"clear-basis scenario references non-clear claim {claim_id}")
            if scenario.get("basis") == "human_decision" and classification == "clear":
                raise ValueError(f"human-decision scenario references clear claim {claim_id}")

    required = {
        claim_id for claim_id, claim in claims.items()
        if claim["classification"] == "clear" and claim["material"] and claim["testable"]
    }
    exceptions = {
        claim_id for claim_id in required
        if isinstance(claims[claim_id].get("coverage_exception"), str)
        and claims[claim_id]["coverage_exception"].strip()
    }
    covered = {claim_id for claim_id in required if mapped[claim_id]}
    missing = required - covered - exceptions
    if missing:
        raise ValueError("material clear claims lack scenarios or coverage exceptions: " + ", ".join(sorted(missing)))
    return {
        "inventory": inventory_path.as_posix(),
        "required": sorted(required),
        "scenario_covered": sorted(covered),
        "coverage_exceptions": sorted(exceptions),
        "mapping_coverage": len(covered) / len(required) if required else 1.0,
    }
