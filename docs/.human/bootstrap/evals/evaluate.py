"""Check declared plan coverage against a scenario. This is not an LLM quality judge."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LIST_FIELDS = {"security_modules", "controls", "capabilities", "blocked_actions"}


def grade(scenario: dict[str, Any], candidate: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(candidate, dict): return ["candidate must be an object"]
    required = {"scenario", "main_effort", "local_discovery", "needs_owner_decision", "rationale"} | LIST_FIELDS
    if set(candidate) != required: return ["candidate fields do not match the rubric contract"]
    if candidate["scenario"] != scenario["id"]: errors.append("wrong scenario")
    for name in LIST_FIELDS:
        values = candidate[name]
        if not isinstance(values, list) or any(not isinstance(x, str) for x in values) or len(values) != len(set(values)):
            errors.append("invalid list: " + name)
    if errors: return errors
    if type(candidate["needs_owner_decision"]) is not bool: errors.append("invalid owner-decision flag")
    if not isinstance(candidate["rationale"], str) or not candidate["rationale"].strip(): errors.append("missing rationale")
    expected = scenario["expected"]
    for name in ["main_effort", "local_discovery"]:
        if candidate[name] not in expected[name]: errors.append("unexpected " + name)
    for rule, field in [("required_modules", "security_modules"), ("required_controls", "controls"), ("required_blocked_actions", "blocked_actions")]:
        missing = set(expected.get(rule, [])) - set(candidate[field])
        if missing: errors.append(rule + " missing: " + ", ".join(sorted(missing)))
    forbidden = set(expected.get("forbidden_capabilities", [])) & set(candidate["capabilities"])
    if forbidden: errors.append("unnecessary capabilities: " + ", ".join(sorted(forbidden)))
    if set(candidate["blocked_actions"]) & set(candidate["capabilities"]): errors.append("blocked actions are also enabled capabilities")
    if expected.get("needs_owner_decision") and not candidate["needs_owner_decision"]:
        errors.append("unresolved owner decision not surfaced")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--candidate", required=True, type=Path)
    args = parser.parse_args()
    scenarios = json.loads((HERE / "scenarios.json").read_text())["scenarios"]
    matches = [s for s in scenarios if s["id"] == args.scenario]
    if not matches: parser.error("unknown scenario")
    if args.candidate.stat().st_size > 1024 * 1024: parser.error("candidate exceeds 1 MiB")
    errors = grade(matches[0], json.loads(args.candidate.read_text()))
    for error in errors: print("FAIL:", error)
    if not errors: print("PASS: declared coverage only; a human must review reasoning, evidence and actual implementation.")
    return int(bool(errors))


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, ValueError, TypeError) as error: raise SystemExit("Invalid candidate: " + str(error))
