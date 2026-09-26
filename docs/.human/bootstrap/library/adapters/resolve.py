"""Resolve BootCrate consumption and execution settings without applying them.

The resolver is deterministic and declarative. It never launches an executor,
changes native settings, or treats a permission profile as task authorization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROFILES = ("protected_manual", "protected_auto", "full_access")
PRESETS = ("standard", "economy")
OVERRIDE_SCHEMA = "bootcrate-execution-profile-override/v1"
PRESET_OVERRIDE_SCHEMA = "bootcrate-preset-override/v1"


def load_json(path: Path) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate JSON key: " + key)
            value[key] = item
        return value
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object: " + str(path))
    return data


def parse_execution_override(value: dict[str, Any]) -> str:
    if set(value) - {"schema", "profile", "risk_acknowledged"}:
        raise ValueError("Unknown execution override field")
    profile = value.get("profile")
    if value.get("schema") != OVERRIDE_SCHEMA or profile not in PROFILES:
        raise ValueError("Invalid execution-profile override")
    if profile == "full_access" and value.get("risk_acknowledged") is not True:
        raise ValueError("Full Access requires explicit risk acknowledgement")
    return profile


def resolve_execution(*, task: str | None = None, task_risk_acknowledged: bool = False,
                      local: dict[str, Any] | None = None) -> dict[str, str]:
    if task:
        if task not in PROFILES:
            raise ValueError("Invalid task execution profile")
        if task == "full_access" and not task_risk_acknowledged:
            raise ValueError("Full Access task override requires explicit risk acknowledgement")
        return {"requested": task, "source": "task"}
    if local is not None:
        return {"requested": parse_execution_override(local), "source": "local"}
    return {"requested": "protected_manual", "source": "safe_default"}


def resolve_preset(*, task: str | None = None, local: str | None = None,
                   project: str | None = None) -> dict[str, str]:
    for source, value in (("task", task), ("local", local), ("project", project), ("default", "standard")):
        if value:
            if value not in PRESETS:
                raise ValueError("Invalid consumption preset from " + source)
            return {"preset": value, "source": source}
    raise AssertionError("unreachable")


def parse_preset_override(value: dict[str, Any]) -> str:
    if set(value) != {"schema", "preset"} or value.get("schema") != PRESET_OVERRIDE_SCHEMA or value.get("preset") not in PRESETS:
        raise ValueError("Invalid consumption-preset override")
    return value["preset"]


def map_request(adapter: dict[str, Any], surface: str, resolved: dict[str, str],
                observation: dict[str, Any] | None = None,
                managed_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    requested = resolved["requested"]
    if adapter.get("id") not in {"codex", "claude_code"}:
        raise ValueError("Unsupported executor adapter")
    profile = adapter.get("execution_permissions", {}).get("profiles", {}).get(requested)
    if not isinstance(profile, dict):
        raise ValueError("Adapter lacks requested execution profile")
    status = profile.get("surfaces", {}).get(surface, "unsupported")
    if status not in {"supported", "unsupported", "unknown"}:
        raise ValueError("Invalid adapter support status")
    reason = profile.get("limits")
    allowed = (managed_policy or {}).get("allowed_profiles")
    if allowed is not None:
        if not isinstance(allowed, list) or any(item not in PROFILES for item in allowed):
            raise ValueError("Invalid managed-policy profile allowlist")
        if requested not in allowed:
            status, reason = "unsupported", "Managed policy does not allow the requested profile."
    policy_blocked = status == "unsupported" and allowed is not None and requested not in allowed
    effective = None
    if observation is not None:
        observed_status = observation.get("status")
        observed_effective = observation.get("effective")
        if observed_status not in {"supported", "unsupported", "unknown"}:
            raise ValueError("Invalid observed support status")
        if observed_effective is not None and observed_effective not in PROFILES:
            raise ValueError("Invalid observed effective profile")
        if observation.get("surface", surface) != surface:
            raise ValueError("Observation belongs to another surface")
        if not policy_blocked:
            status, effective = observed_status, observed_effective
            reason = observation.get("reason") or reason
            # An observed profile cannot satisfy a different requested profile,
            # even when the observation describes broader permissions.
            if effective is not None and effective != requested:
                status, effective = ("unsupported" if status == "unsupported" else "unknown"), None
                reason = ("Observed effective profile " + observed_effective +
                          " does not match requested profile " + requested + ".")
            elif adapter["id"] == "codex" and requested == "protected_auto":
                capabilities = observation.get("capabilities") or {}
                if not isinstance(capabilities, dict):
                    raise ValueError("Invalid Codex capability observation")
                auto_review = capabilities.get("approvals_reviewer_auto_review")
                if auto_review is False:
                    status, effective = "unsupported", None
                    reason = "Codex client does not support approvals_reviewer = auto_review on this surface."
                elif auto_review is not True or observation.get("surface") != surface:
                    status, effective = ("unsupported" if status == "unsupported" else "unknown"), None
                    reason = "Codex Protected Auto not proven: matching surface and approvals_reviewer = auto_review support are required."
                elif status != "supported":
                    effective = None
            elif adapter["id"] == "claude_code" and requested == "full_access" and effective == "full_access":
                capabilities = observation.get("capabilities") or {}
                if not isinstance(capabilities, dict):
                    raise ValueError("Invalid Claude capability observation")
                missing = [name for name in ("approval_bypass", "filesystem_unrestricted", "network_unrestricted")
                           if capabilities.get(name) is not True]
                if observation.get("surface") != surface:
                    missing.insert(0, "observed surface")
                if status != "supported" or missing:
                    status, effective = "unknown", None
                    reason = "Claude Full Access not proven: " + ", ".join(missing or ["supported status"]) + "."
            if status != "supported":
                effective = None
    return {
        "requested": requested,
        "effective": effective,
        "source": resolved["source"],
        "executor": adapter["id"],
        "surface": surface,
        "status": status,
        "applied": status == "supported" and effective == requested,
        "native_action": {"cli_args": profile.get("cli_args", []), "settings_patch": profile.get("native_settings", {})},
        "reason": reason,
        "authorization": "Technical permissions do not authorize push, publication, production changes, purchases, or secret access."
    }


def local_override_path(project_root: Path) -> Path:
    root = project_root.resolve(strict=True)
    target = root / ".local" / "config" / "execution-profile.json"
    if not target.resolve(strict=False).is_relative_to(root):
        raise ValueError("Unsafe local override path")
    return target


def local_preset_path(project_root: Path) -> Path:
    root = project_root.resolve(strict=True)
    target = root / ".local" / "config" / "preset.json"
    if not target.resolve(strict=False).is_relative_to(root):
        raise ValueError("Unsafe local preset path")
    return target


def clear_local_override(project_root: Path) -> bool:
    target = local_override_path(project_root)
    if target.is_symlink():
        raise ValueError("Refusing to remove a linked override")
    if not target.exists():
        return False
    if not target.is_file():
        raise ValueError("Local override is not a regular file")
    target.unlink()
    return True


def clear_local_preset(project_root: Path) -> bool:
    target = local_preset_path(project_root)
    if target.is_symlink():
        raise ValueError("Refusing to remove a linked preset override")
    if not target.exists():
        return False
    if not target.is_file():
        raise ValueError("Local preset override is not a regular file")
    target.unlink()
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--surface", required=True)
    parser.add_argument("--task-profile", choices=PROFILES)
    parser.add_argument("--task-preset", choices=PRESETS)
    parser.add_argument("--project-profile", type=Path)
    parser.add_argument("--acknowledge-full-access-risk", action="store_true")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--clear-local", action="store_true")
    parser.add_argument("--clear-local-preset", action="store_true")
    args = parser.parse_args()
    override_path = local_override_path(args.project_root)
    if args.clear_local:
        clear_local_override(args.project_root)
    if args.clear_local_preset:
        clear_local_preset(args.project_root)
    local = load_json(override_path) if override_path.exists() else None
    resolved = resolve_execution(task=args.task_profile,
                                 task_risk_acknowledged=args.acknowledge_full_access_risk,
                                 local=local)
    preset_path = local_preset_path(args.project_root)
    local_preset = parse_preset_override(load_json(preset_path)) if preset_path.exists() else None
    project_preset = None
    if args.project_profile:
        project_preset = load_json(args.project_profile).get("workflow", {}).get("consumption_preset")
    consumption = resolve_preset(task=args.task_preset, local=local_preset, project=project_preset)
    consumption.update({"effective":None,"status":"prepared","applied":False,
                        "application":"The orchestrator uses this strategy for optional context/delegation; no client setting is claimed."})
    print(json.dumps({"execution":map_request(load_json(args.adapter), args.surface, resolved),
                      "consumption":consumption}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
