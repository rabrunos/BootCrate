"""Resolve BootCrate consumption and execution settings without applying them.

The resolver is deterministic and declarative. It never launches an executor,
changes native settings, or treats a permission profile as task authorization.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import importlib.util
import json
import os
import secrets
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

PROFILES = ("protected_manual", "protected_auto", "full_access")
PRESETS = ("standard", "economy")
OVERRIDE_SCHEMA = "bootcrate-execution-profile-override/v1"
PRESET_OVERRIDE_SCHEMA = "bootcrate-preset-override/v1"
MAX_LOCAL_OVERRIDE_BYTES = 64 * 1024
_RENAME_NOREPLACE = 1
REVIEWED_PERMISSION_MAPPINGS = {
    "codex": "502e630e40e074999bad7ce4c6c1a7e4f40ff42571d3a1f960ce6b841c81e74b",
    "claude_code": "8e60fcc683aeb5d818040648ed81260cde72e7082c1a2b631bc5566b6047092a",
}


def _parse_json(text: str, source: str) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate JSON key")
            value[key] = item
        return value
    data = json.loads(text, object_pairs_hook=no_duplicates)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object: " + source)
    return data


def load_json(path: Path) -> dict[str, Any]:
    return _parse_json(path.read_text(encoding="utf-8"), path.name)


def parse_execution_override(value: dict[str, Any]) -> str:
    if not isinstance(value, dict):
        raise ValueError("Invalid execution-profile override")
    if set(value) - {"schema", "profile", "risk_acknowledged"}:
        raise ValueError("Unknown execution override field")
    if "risk_acknowledged" in value and type(value["risk_acknowledged"]) is not bool:
        raise ValueError("Invalid execution override risk acknowledgement")
    profile = value.get("profile")
    if value.get("schema") != OVERRIDE_SCHEMA or profile not in PROFILES:
        raise ValueError("Invalid execution-profile override")
    if profile == "full_access" and value.get("risk_acknowledged") is not True:
        raise ValueError("Full Access requires explicit risk acknowledgement")
    return profile


def resolve_execution(*, task: str | None = None, task_risk_acknowledged: bool = False,
                      local: dict[str, Any] | None = None) -> dict[str, str]:
    if type(task_risk_acknowledged) is not bool:
        raise ValueError("Invalid task risk acknowledgement")
    if task:
        if task not in PROFILES:
            raise ValueError("Invalid task execution profile")
        if task == "full_access" and task_risk_acknowledged is not True:
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
    if (not isinstance(value, dict) or set(value) != {"schema", "preset"} or
            value.get("schema") != PRESET_OVERRIDE_SCHEMA or value.get("preset") not in PRESETS):
        raise ValueError("Invalid consumption-preset override")
    return value["preset"]


def _validate_permission_mapping(adapter: dict[str, Any]) -> None:
    """Bind executable native actions to the reviewed adapter permission maps."""
    if not isinstance(adapter, dict) or adapter.get("schema") != "bootcrate-adapter/v1":
        raise ValueError("Invalid executor adapter")
    executor = adapter.get("id")
    if executor not in REVIEWED_PERMISSION_MAPPINGS:
        raise ValueError("Unsupported executor adapter")
    try:
        encoded = json.dumps({"id": executor,
                              "execution_permissions": adapter["execution_permissions"]},
                             sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid executor adapter permission mapping") from error
    if hashlib.sha256(encoded).hexdigest() != REVIEWED_PERMISSION_MAPPINGS[executor]:
        raise ValueError("Unreviewed executor adapter permission mapping")


def map_request(adapter: dict[str, Any], surface: str, resolved: dict[str, str],
                observation: dict[str, Any] | None = None,
                managed_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    _validate_permission_mapping(adapter)
    requested = resolved["requested"]
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
        if observation.get("executor") not in (None, adapter["id"]):
            raise ValueError("Observation belongs to another executor")
        if observation.get("surface") not in (None, surface):
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
                    status, effective = ("unsupported" if status == "unsupported" else "unknown"), None
                    reason = "Claude Full Access not proven: " + ", ".join(missing or ["supported status"]) + "."
            if status != "supported":
                effective = None
            if observation.get("executor") is None:
                status, effective = ("unsupported" if status == "unsupported" else "unknown"), None
                reason = "Permission observation has no observed executor; requested " + adapter["id"] + " is not proven."
            if observation.get("surface") is None:
                status, effective = ("unsupported" if status == "unsupported" else "unknown"), None
                reason = "Permission observation has no observed surface; requested " + surface + " is not proven."
    return {
        "requested": requested,
        "effective": effective,
        "source": resolved["source"],
        "executor": adapter["id"],
        "surface": surface,
        "status": status,
        "applied": status == "supported" and effective == requested,
        "native_action": (None if status == "unsupported" else {
            "cli_args": profile.get("cli_args", []),
            "settings_patch": profile.get("native_settings", {}),
        }),
        "reason": reason,
        "authorization": "Technical permissions do not authorize push, publication, production changes, purchases, or secret access."
    }


def _local_config_path(project_root: Path, filename: str) -> Path:
    root = project_root.resolve(strict=True)
    local = root / ".local"
    config = local / "config"
    # Both parents must be actual directories, even when a link resolves to
    # another location inside the project root.
    for parent in (local, config):
        try:
            metadata = parent.lstat()
        except FileNotFoundError:
            continue
        reparse = (getattr(metadata, "st_file_attributes", 0) &
                   getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
        if stat.S_ISLNK(metadata.st_mode) or reparse:
            raise ValueError("Unsafe linked local config directory")
        if not stat.S_ISDIR(metadata.st_mode):
            raise ValueError("Local config parent is not a directory")
    target = config / filename
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        metadata = None
    if metadata is not None:
        reparse = (getattr(metadata, "st_file_attributes", 0) &
                   getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
        if stat.S_ISLNK(metadata.st_mode) or reparse or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("Local override must be a regular, unlinked file")
        if metadata.st_size > MAX_LOCAL_OVERRIDE_BYTES:
            raise ValueError("Local override exceeds its size limit")
    if not target.resolve(strict=False).is_relative_to(root):
        raise ValueError("Unsafe local config path")
    return target


def local_override_path(project_root: Path) -> Path:
    return _local_config_path(project_root, "execution-profile.json")


def local_preset_path(project_root: Path) -> Path:
    return _local_config_path(project_root, "preset.json")


def _windows_mutation_module():
    adjacent = Path(__file__).with_name("_windows_mutation.py")
    bootstrap = Path(__file__).resolve().parents[2] / "upgrade" / "_windows_mutation.py"
    helper = next((path for path in (adjacent, bootstrap) if path.is_file()), None)
    if helper is None:
        raise OSError("Safe local override access requires the Windows native mutation helper")
    spec = importlib.util.spec_from_file_location("_bootcrate_windows_mutation", helper)
    if spec is None or spec.loader is None:
        raise OSError("Windows native mutation helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_local_bytes(project_root: Path, filename: str) -> bytes | None:
    root = project_root.resolve(strict=True)
    relative = Path(".local") / "config" / filename
    if os.name == "nt":
        with _windows_mutation_module().WindowsMutator(root) as mutator:
            return mutator.read(relative, max_bytes=MAX_LOCAL_OVERRIDE_BYTES, missing_ok=True)

    if (not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")) or
            os.open not in os.supports_dir_fd):
        raise OSError("Safe local override read requires directory-relative no-follow open")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    leaf_flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    handles = []
    try:
        root_fd = os.open(root, directory_flags)
        handles.append(root_fd)
        parent_fd = root_fd
        for component in (".local", "config"):
            try:
                parent_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            except FileNotFoundError:
                return None
            handles.append(parent_fd)
        try:
            leaf_fd = os.open(filename, leaf_flags, dir_fd=parent_fd)
        except FileNotFoundError:
            return None
        handles.append(leaf_fd)
        metadata = os.fstat(leaf_fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("Local override must be a regular, unlinked file")
        if metadata.st_size > MAX_LOCAL_OVERRIDE_BYTES:
            raise ValueError("Local override exceeds its size limit")
        with os.fdopen(os.dup(leaf_fd), "rb") as stream:
            content = stream.read(MAX_LOCAL_OVERRIDE_BYTES + 1)
        if len(content) > MAX_LOCAL_OVERRIDE_BYTES:
            raise ValueError("Local override exceeds its size limit")
        return content
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise ValueError("Unsafe linked local override path") from error
        raise
    finally:
        for handle in reversed(handles):
            os.close(handle)


def _load_local_config(project_root: Path, filename: str) -> dict[str, Any] | None:
    _reject_tracked_local_config(project_root, filename)
    _local_config_path(project_root, filename)
    content = _read_local_bytes(project_root, filename)
    return None if content is None else _parse_json(content.decode("utf-8"), filename)


def _reject_tracked_local_config(project_root: Path, filename: str) -> None:
    root = project_root.resolve(strict=True)
    if not any((parent / ".git").exists() or (parent / ".git").is_symlink()
               for parent in (root, *root.parents)):
        return
    relative = ".local/config/" + filename
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        worktree = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"], cwd=root,
            capture_output=True, check=True, timeout=10, env=environment)
        if worktree.stdout.strip() != b"true":
            raise ValueError("Machine-local configuration requires a Git worktree")
        result = subprocess.run(
            ["git", "ls-files", "--cached", "-z", "--", ":(icase,literal)" + relative],
            cwd=root, capture_output=True, check=True, timeout=10,
            env=environment)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        raise ValueError("Cannot verify Git tracking for machine-local configuration") from error
    if relative.encode("ascii") in (entry.lower() for entry in result.stdout.split(b"\0")):
        raise ValueError("Tracked machine-local configuration is invalid: " + relative)


def _rename_local_noreplace(parent_fd: int, source: str, destination: str) -> None:
    """Move a local leaf without replacing a concurrent entry (Linux only)."""
    if sys.platform != "linux":
        raise OSError("Safe local override removal requires Linux renameat2")
    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except AttributeError as error:
        raise OSError("Safe local override removal requires renameat2") from error
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                          ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    if renameat2(parent_fd, os.fsencode(source), parent_fd,
                 os.fsencode(destination), _RENAME_NOREPLACE):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), source)


def _unlink_local_file(target: Path, expected_identity: tuple[int, int]) -> None:
    root = target.parents[2]
    relative = Path(".local") / "config" / target.name
    if os.name == "nt":
        with _windows_mutation_module().WindowsMutator(root) as mutator:
            mutator.unlink(relative, expected_identity=expected_identity)
        return

    if (not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")) or
            any(method not in os.supports_dir_fd for method in (os.open, os.stat))):
        raise OSError("Safe local override removal requires directory-relative operations")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    root_fd = os.open(root, flags)
    try:
        local_fd = os.open(".local", flags, dir_fd=root_fd)
        try:
            config_fd = os.open("config", flags, dir_fd=local_fd)
            try:
                leaf_flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
                leaf_fd = os.open(target.name, leaf_flags, dir_fd=config_fd)
                try:
                    metadata = os.fstat(leaf_fd)
                    if not stat.S_ISREG(metadata.st_mode) or (metadata.st_dev, metadata.st_ino) != expected_identity:
                        raise ValueError("Local override changed before removal")
                    displaced = ".clear-" + secrets.token_hex(16)
                    _rename_local_noreplace(config_fd, target.name, displaced)
                    moved = os.stat(displaced, dir_fd=config_fd, follow_symlinks=False)
                    if not stat.S_ISREG(moved.st_mode) or (moved.st_dev, moved.st_ino) != expected_identity:
                        try:
                            _rename_local_noreplace(config_fd, displaced, target.name)
                        except OSError as error:
                            raise ValueError("Local override changed; replacement preserved as " + displaced) from error
                        raise ValueError("Local override changed before removal")
                    # POSIX cannot unlink a regular file by its open descriptor.
                    # Keep the verified old override under the ignored local
                    # quarantine name; a concurrent replacement of that name
                    # must never be removed by a pathname-based unlink.
                finally:
                    os.close(leaf_fd)
            finally:
                os.close(config_fd)
        finally:
            os.close(local_fd)
    finally:
        os.close(root_fd)


def clear_local_override(project_root: Path) -> bool:
    _reject_tracked_local_config(project_root, "execution-profile.json")
    target = local_override_path(project_root)
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return False
    reparse = (getattr(metadata, "st_file_attributes", 0) &
               getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    if stat.S_ISLNK(metadata.st_mode) or reparse:
        raise ValueError("Refusing to remove a linked override")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("Local override is not a regular file")
    if metadata.st_size > MAX_LOCAL_OVERRIDE_BYTES:
        raise ValueError("Local override exceeds its size limit")
    _unlink_local_file(target, (metadata.st_dev, metadata.st_ino))
    return True


def clear_local_preset(project_root: Path) -> bool:
    _reject_tracked_local_config(project_root, "preset.json")
    target = local_preset_path(project_root)
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return False
    reparse = (getattr(metadata, "st_file_attributes", 0) &
               getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    if stat.S_ISLNK(metadata.st_mode) or reparse:
        raise ValueError("Refusing to remove a linked preset override")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("Local preset override is not a regular file")
    if metadata.st_size > MAX_LOCAL_OVERRIDE_BYTES:
        raise ValueError("Local override exceeds its size limit")
    _unlink_local_file(target, (metadata.st_dev, metadata.st_ino))
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
    # Validate every requested clear before either file can be moved or removed.
    if args.clear_local:
        _reject_tracked_local_config(args.project_root, "execution-profile.json")
    if args.clear_local_preset:
        _reject_tracked_local_config(args.project_root, "preset.json")
    if args.clear_local:
        clear_local_override(args.project_root)
    if args.clear_local_preset:
        clear_local_preset(args.project_root)
    local = None if args.task_profile else _load_local_config(args.project_root, "execution-profile.json")
    resolved = resolve_execution(task=args.task_profile,
                                 task_risk_acknowledged=args.acknowledge_full_access_risk,
                                 local=local)
    local_preset_data = None if args.task_preset else _load_local_config(args.project_root, "preset.json")
    local_preset = parse_preset_override(local_preset_data) if local_preset_data is not None else None
    project_preset = None
    if args.project_profile:
        workflow = load_json(args.project_profile).get("workflow", {})
        if not isinstance(workflow, dict):
            raise ValueError("Invalid project workflow configuration")
        project_preset = workflow.get("consumption_preset")
    consumption = resolve_preset(task=args.task_preset, local=local_preset, project=project_preset)
    consumption.update({"effective":None,"status":"prepared","applied":False,
                        "application":"The orchestrator uses this strategy for optional context/delegation; no client setting is claimed."})
    print(json.dumps({"execution":map_request(load_json(args.adapter), args.surface, resolved),
                      "consumption":consumption}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        raise SystemExit(2)
    except OSError:
        print("BLOCKED: Cannot read resolver input or local configuration", file=sys.stderr)
        raise SystemExit(2)
