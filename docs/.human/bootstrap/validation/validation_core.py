"""Shared, read-only profile and repository checks for template and downstream validation."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tomllib
from typing import Any

from jsonschema import Draft202012Validator


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def local_refs_only(node: Any) -> None:
    if isinstance(node, dict):
        if "$ref" in node:
            require(isinstance(node["$ref"], str) and node["$ref"].startswith("#"),
                    "Validation must not fetch remote schema references")
        for value in node.values():
            local_refs_only(value)
    elif isinstance(node, list):
        for value in node:
            local_refs_only(value)


def schema_check(schema: dict[str, Any], value: Any) -> None:
    local_refs_only(schema)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    require(not errors, "Schema failure at " + (str(list(errors[0].path)) if errors else "root"))


def profile_schema(schema_dir: Path, profile: dict[str, Any]) -> dict[str, Any]:
    version = profile.get("schema")
    names = {"project-profile/v2": "project-profile-v2.schema.json",
             "project-profile/v3": "project-profile.schema.json"}
    require(version in names, "Unsupported project profile schema")
    return load_json(schema_dir / names[version])


def project_file(root: Path, relative: str, label: str) -> Path:
    require(isinstance(relative, str) and relative and "<" not in relative and "\\" not in relative,
            f"Invalid {label} reference")
    path = Path(relative)
    require(not path.is_absolute() and not any(part in {"..", ".git", ".local"} for part in path.parts),
            f"Unsafe {label} reference")
    current = root.resolve()
    for part in path.parts:
        current = current / part
        require(not current.is_symlink(), f"Symlink in {label} reference")
    require(current.resolve().is_relative_to(root.resolve()) and current.is_file(), f"Missing {label}: {relative}")
    return current


VERSION_TOKEN = re.compile(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,127}")


def _value_at(value: Any, pointer: str, label: str) -> Any:
    require(isinstance(pointer, str) and pointer.startswith("/"), f"Invalid {label} value path")
    current = value
    for raw in pointer.split("/")[1:]:
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            require(key in current, f"Missing {label} value at {pointer}")
            current = current[key]
        elif isinstance(current, list) and key.isdigit():
            index = int(key)
            require(index < len(current), f"Missing {label} value at {pointer}")
            current = current[index]
        else:
            raise ValueError(f"Missing {label} value at {pointer}")
    return current


def version_value(root: Path, source: dict[str, Any], label: str = "canonical version") -> str:
    """Read a version declaratively; never execute a command from the profile."""
    path = project_file(root, source.get("path", ""), label)
    reader = source.get("reader")
    require(reader in {"plain", "json", "toml"}, f"Unsupported {label} reader")
    require(path.stat().st_size <= 1024 * 1024, f"{label.capitalize()} source is too large")
    if reader == "plain":
        value: Any = path.read_text(encoding="utf-8").strip()
    elif reader == "json":
        value = _value_at(load_json(path), source.get("value_path", ""), label)
    else:
        with path.open("rb") as stream:
            value = _value_at(tomllib.load(stream), source.get("value_path", ""), label)
    require(not isinstance(value, bool) and isinstance(value, (str, int, float)),
            f"{label.capitalize()} value must be scalar")
    token = str(value).strip()
    require(VERSION_TOKEN.fullmatch(token) is not None, f"Invalid {label} value")
    return token


def _version_contract(profile: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], str, str]:
    versioning = profile["versioning"]
    if profile["schema"] == "project-profile/v2":
        suffix = Path(versioning["canonical_source"]).suffix.lower()
        reader = "json" if suffix == ".json" else "toml" if suffix == ".toml" else "plain"
        source = {"path": versioning["canonical_source"], "reader": reader}
        return source, [], "CHANGELOG.md", "markdown-headings"
    source = {"path": versioning["canonical_source"], "reader": versioning["reader"]}
    if "value_path" in versioning:
        source["value_path"] = versioning["value_path"]
    return source, versioning["mirrors"], versioning["history_source"], versioning["history_format"]


def validate_version_contract(profile: dict[str, Any], root: Path) -> str:
    source, mirrors, history_source, history_format = _version_contract(profile)
    version = version_value(root, source)
    for mirror in mirrors:
        require(version_value(root, mirror, "version mirror") == version,
                "Canonical version and mirror diverge: " + mirror["path"])
    history = project_file(root, history_source, "canonical version history")
    require(history_format == "markdown-headings", "Unsupported canonical history reader")
    require(history.stat().st_size <= 2 * 1024 * 1024, "Canonical version history is too large")
    heading = re.compile(
        r"^##\s+\[?v?" + re.escape(version) + r"\]?(?:\s|$|[—:–-])",
        re.MULTILINE,
    )
    require(heading.search(history.read_text(encoding="utf-8")) is not None,
            "Canonical history has no entry for integrated version " + version)
    return version


def materialized_profile(profile: dict[str, Any], root: Path | None = None) -> None:
    """Finalization gate. A valid draft is not necessarily a completed project."""
    def walk(value: Any) -> None:
        if isinstance(value, str):
            require("<materialize>" not in value and value.strip().lower() not in {"tbd", "unknown"},
                    "Unresolved materialization value")
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    # 'unknown' is allowed for fields not involved in the finalized decision, e.g. no such field.
    walk(profile)
    require(profile["workflow"]["tracking"] == "github_issues" and
            profile["workflow"]["primary_orchestrator"] == "chatgpt",
            "Finalized method requires GitHub Issues and ChatGPT orchestration")
    require(profile["security"]["exposure"] != "unknown", "Unresolved security exposure")
    for service in profile.get("services", []):
        require(service["operator"].strip().lower() not in {"unknown", "tbd", "none"},
                "Service operator is unresolved")
    if profile["schema"] == "project-profile/v3":
        distribution = profile["distribution"]
        require(distribution["mode"] == "none" or bool(distribution["targets"]),
                "Distribution enabled without a destination")
        require(distribution["mode"] != "none" or not distribution["targets"],
                "Distribution destination declared for a project without distribution")
        targets = [(target["id"], target["channel"]) for target in distribution["targets"]]
        require(len(targets) == len(set(targets)), "Duplicate distribution destination/channel")
        if distribution["mode"] in {"artifact", "deployment"}:
            require(all(t["kind"] == distribution["mode"] for t in distribution["targets"]),
                    "Distribution mode and selected targets disagree")
    if root is not None:
        validate_version_contract(profile, root)
        project_file(root, profile["security"]["control_map"], "security control map")
        project_file(root, "PROJECT_GUIDE.md", "project guide")
        for required in profile.get("validation", {}).get("required_files", []):
            project_file(root, required, "declared required file")
        locations = {"codex": ("AGENTS.md", ".agents/skills", ".codex/config.toml"),
                     "claude_code": ("CLAUDE.md", ".claude/skills", ".claude/settings.json")}
        for harness in profile["workflow"]["implementation_harnesses"]:
            entry, skills, native_config = locations[harness]
            project_file(root, entry, "enabled executor instructions")
            project_file(root, native_config, "enabled executor configuration")
            for skill in profile.get("skills", []):
                require(re.fullmatch(r"[a-z0-9-]+", skill) is not None, "Invalid selected skill name")
                project_file(root, f"{skills}/{skill}/SKILL.md", "selected executor skill")


EXAMPLES = {".env.example", ".env.sample", ".env.template"}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b"),
]


def sensitive_name(path: Path) -> bool:
    name = path.name.lower()
    if name in EXAMPLES or name.startswith(("secrets.example.", "credentials.example.")):
        return False
    return (name == ".env" or name.startswith((".env.", "secrets.", "credentials.")) or
            name in {"id_rsa", "id_ed25519", "id_ecdsa"} or path.suffix.lower() in {".key", ".p12", ".pfx"})


def secret_findings(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def inventory(root: Path) -> tuple[list[Path], list[Path]]:
    """Return tracked and untracked (not ignored) paths, without reading ignored files."""
    if (root / ".git").exists():
        def listed(*args: str) -> list[Path]:
            result = subprocess.run(["git", "ls-files", "-z", *args], cwd=root,
                                    capture_output=True, timeout=30, check=True)
            return [root / n.decode("utf-8") for n in result.stdout.split(b"\0") if n]
        return listed("--cached"), listed("--others", "--exclude-standard")
    skip = {".git", ".local", ".venv", "__pycache__", "node_modules", ".temp"}
    return [], [p for p in root.rglob("*") if (p.is_file() or p.is_symlink())
                and not (set(p.relative_to(root).parts) & skip)]
