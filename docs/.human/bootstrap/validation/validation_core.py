"""Shared, read-only profile and repository checks for template and downstream validation."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tomllib
from typing import Any

from jsonschema import Draft202012Validator
import yaml


class UniqueLoader(yaml.SafeLoader):
    """Safe YAML with duplicate rejection and YAML-1.2-style booleans."""


UniqueLoader.yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for key, entries in UniqueLoader.yaml_implicit_resolvers.items():
    UniqueLoader.yaml_implicit_resolvers[key] = [entry for entry in entries
                                                   if entry[0] != "tag:yaml.org,2002:bool"]
UniqueLoader.add_implicit_resolver("tag:yaml.org,2002:bool",
                                   re.compile(r"^(?:true|false|True|False|TRUE|FALSE)$"), list("tTfF"))


def _unique_mapping(loader: UniqueLoader, node: Any, deep: bool = False) -> dict[str, Any]:
    loader.flatten_mapping(node)
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def load_yaml(text: str) -> Any:
    return yaml.load(text, Loader=UniqueLoader)


CLAUDE_CREDENTIAL_DENY_RULES = frozenset({
    "Read(./.env)", "Read(./.env.*)", "Read(./**/.env)", "Read(./**/.env.*)",
    "Read(./**/secrets.*)", "Read(./**/credentials.*)", "Read(./**/*.key)",
    "Read(./**/*.p12)", "Read(./**/*.pfx)",
})


ALLOWED_CODEX_CONFIG_KEYS = {
    "model_reasoning_effort": None,
    "approval_policy": None,
    "approvals_reviewer": None,
    "sandbox_mode": None,
    "agents": {"enabled", "max_concurrent_threads_per_session", "interrupt_message"},
    "sandbox_workspace_write": {"network_access", "writable_roots"},
    "shell_environment_policy": {"inherit", "ignore_default_excludes"},
}


ALLOWED_CLAUDE_CONFIG_KEYS = {
    "$schema": None,
    "effortLevel": None,
    "permissions": {"defaultMode", "deny"},
    "sandbox": {"enabled", "allowUnsandboxedCommands"},
}


CODEX_AGENT_SANDBOXES = {"scout": "read-only", "worker": "workspace-write"}
CODEX_AGENT_EFFORTS = {"scout": "medium", "worker": "low"}
CODEX_AGENT_INSTRUCTIONS_SHA256 = {
    "scout": "c2499fae1d2a3bc3be41aada8038184432d784419c953ebd4b6e6ceb35e8c35a",
    "worker": "ce445d89179c868978504ad8fee815f1a835a37a6b7c4d4a15325a5139fca3fb",
}
ALLOWED_CODEX_AGENT_KEYS = {
    "name", "description", "developer_instructions", "model", "model_reasoning_effort", "sandbox_mode",
}


def validate_codex_agent_configs(root: Path) -> None:
    """Bound optional v3 Codex roles to the selected Scout/Worker permissions."""
    agents = root / ".codex/agents"
    if not (agents.exists() or agents.is_symlink() or getattr(agents, "is_junction", lambda: False)()):
        return
    require(agents.is_dir() and not agents.is_symlink() and
            not getattr(agents, "is_junction", lambda: False)(),
            "Codex agent directory must be local and real")
    for path in agents.iterdir():
        role = path.stem
        require(path.name == role + ".toml" and role in CODEX_AGENT_SANDBOXES,
                "Unselected Codex agent configuration: " + path.name)
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2 * 1024 * 1024,
                "Codex agent configuration is linked, missing or too large: " + path.name)
        settings = tomllib.loads(path.read_text(encoding="utf-8"))
        require(set(settings) <= ALLOWED_CODEX_AGENT_KEYS,
                "Unselected Codex agent configuration key: " + path.name)
        require(settings.get("name") == role and
                all(isinstance(settings.get(key), str) and settings[key].strip()
                    for key in ("description", "developer_instructions")),
                "Invalid Codex agent identity or instructions: " + path.name)
        require(settings.get("sandbox_mode") == CODEX_AGENT_SANDBOXES[role],
                "Unsafe Codex agent sandbox: " + path.name)
        # Role instructions are an executable trust input. Keep the reviewed
        # baseline while allowing a materialized project to choose its model.
        require(hashlib.sha256(settings["developer_instructions"].encode("utf-8")).hexdigest() ==
                CODEX_AGENT_INSTRUCTIONS_SHA256[role],
                "Unreviewed Codex agent instructions: " + path.name)
        require(settings.get("model_reasoning_effort") == CODEX_AGENT_EFFORTS[role],
                "Unexpected Codex agent effort: " + path.name)
        if "model" in settings:
            require(isinstance(settings["model"], str) and bool(settings["model"].strip()),
                    "Invalid Codex agent model: " + path.name)


CLAUDE_AGENT_BASELINE = {
    "scout": {
        "effort": "medium", "maxTurns": 30, "tools": "Read, Grep, Glob",
        "description_sha256": "eeb66ca859b92ed9d3e7739faa3cc10da133e28d17acff0e22acb11826968b9c",
        "body_sha256": "dc7d650d099d0e69df46d727f6b2312cbddeae92239f6d0b091454562ab946a9",
    },
    "worker": {
        "effort": "low", "maxTurns": 20,
        "description_sha256": "d7b33d62722a7b7b3ada66fb361545bbf5cd3eb71f2ce82c4127254dea2433e7",
        "body_sha256": "a1ba3a8425010708de4b4e8ed3b0d15e747b011f0c66cdb76311062a584af112",
    },
}


def validate_claude_agent_configs(root: Path) -> None:
    """Bound optional v3 Claude roles to the reviewed Scout/Worker files."""
    agents = root / ".claude/agents"
    if not (agents.exists() or agents.is_symlink() or getattr(agents, "is_junction", lambda: False)()):
        return
    require(agents.is_dir() and not agents.is_symlink() and
            not getattr(agents, "is_junction", lambda: False)(),
            "Claude agent directory must be local and real")
    for path in agents.iterdir():
        role = path.stem
        require(path.name == role + ".md" and role in CLAUDE_AGENT_BASELINE,
                "Unselected Claude agent configuration: " + path.name)
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2 * 1024 * 1024,
                "Claude agent configuration is linked, missing or too large: " + path.name)
        parts = path.read_text(encoding="utf-8").split("---", 2)
        require(len(parts) == 3 and not parts[0].strip(),
                "Invalid Claude agent frontmatter: " + path.name)
        settings = load_yaml(parts[1])
        baseline = CLAUDE_AGENT_BASELINE[role]
        require(isinstance(settings, dict) and set(settings) ==
                ({"name", "description", "model", "effort", "maxTurns", "tools"}
                 if role == "scout" else {"name", "description", "model", "effort", "maxTurns"}),
                "Unselected Claude agent settings: " + path.name)
        require(settings["name"] == role and settings["effort"] == baseline["effort"] and
                settings["maxTurns"] == baseline["maxTurns"] and
                (role != "scout" or settings["tools"] == baseline["tools"]),
                "Unsafe Claude agent role settings: " + path.name)
        require(isinstance(settings["model"], str) and bool(settings["model"].strip()),
                "Invalid Claude agent model: " + path.name)
        require(isinstance(settings["description"], str) and
                hashlib.sha256(settings["description"].encode("utf-8")).hexdigest() ==
                baseline["description_sha256"] and
                hashlib.sha256(parts[2].encode("utf-8")).hexdigest() == baseline["body_sha256"],
                "Unreviewed Claude agent instructions: " + path.name)


def reject_unselected_codex_config(settings: dict) -> None:
    """Reject v3 native settings outside the selected protected baseline."""
    require(isinstance(settings, dict), "Codex configuration must be a TOML table")
    for key, value in settings.items():
        require(key in ALLOWED_CODEX_CONFIG_KEYS,
                f"Unselected Codex configuration key: {key}")
        allowed_children = ALLOWED_CODEX_CONFIG_KEYS[key]
        if allowed_children is None:
            require(not isinstance(value, dict), f"Unexpected Codex configuration table: {key}")
            continue
        require(isinstance(value, dict), f"Codex configuration table required: {key}")
        for child in value:
            require(child in allowed_children,
                    f"Unselected Codex configuration key: {key}.{child}")


def reject_unselected_claude_config(settings: dict) -> None:
    """Reject executable or undeclared v3 Claude project settings."""
    require(isinstance(settings, dict), "Claude configuration must be a JSON object")
    for key, value in settings.items():
        require(key in ALLOWED_CLAUDE_CONFIG_KEYS,
                f"Unselected Claude configuration key: {key}")
        allowed_children = ALLOWED_CLAUDE_CONFIG_KEYS[key]
        if allowed_children is None:
            require(not isinstance(value, (dict, list)),
                    f"Unexpected Claude configuration structure: {key}")
            continue
        require(isinstance(value, dict), f"Claude configuration object required: {key}")
        for child in value:
            require(child in allowed_children,
                    f"Unselected Claude configuration key: {key}.{child}")


def valid_claude_credential_denials(value: Any) -> bool:
    return (isinstance(value, list) and all(isinstance(rule, str) for rule in value)
            and CLAUDE_CREDENTIAL_DENY_RULES.issubset(value))


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
    path = version_source_file(root, source.get("path", ""), label)
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
    require(not isinstance(value, float) or math.isfinite(value),
            f"{label.capitalize()} numeric value must be finite")
    token = str(value).strip()
    require(VERSION_TOKEN.fullmatch(token) is not None, f"Invalid {label} value")
    return token


def version_source_file(root: Path, relative: str, label: str) -> Path:
    """Keep version metadata away from credential and private-key file names."""
    path = project_file(root, relative, label)
    require(not any(sensitive_name(Path(part)) for part in Path(relative).parts),
            f"Sensitive {label} reference: {relative}")
    return path


def _version_contract(profile: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], str, str]:
    """Return the declarative version contract available only in profile v3."""
    versioning = profile["versioning"]
    source = {"path": versioning["canonical_source"], "reader": versioning["reader"]}
    if "value_path" in versioning:
        source["value_path"] = versioning["value_path"]
    return source, versioning["mirrors"], versioning["history_source"], versioning["history_format"]


def _history_has_heading(markdown: str, heading: re.Pattern[str]) -> bool:
    """Find a history heading outside fences, comments and raw HTML blocks."""
    fence: str | None = None
    in_comment = False
    raw_html = False
    html_until_blank = False
    content_tag = re.compile(r"^ {0,3}<(?:script|pre|style|textarea)(?=[\t >])", re.I)
    content_end = re.compile(r"</(?:script|pre|style|textarea)[ \t]*>", re.I)
    for raw_line in markdown.splitlines():
        if fence is not None:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) +
                            "{" + str(len(fence)) + r",}[ \t]*", raw_line):
                fence = None
            continue
        if raw_html:
            if content_end.search(raw_line):
                raw_html = False
            continue
        if html_until_blank:
            if not raw_line.strip():
                html_until_blank = False
            continue
        if in_comment:
            end = raw_line.find("-->")
            if end < 0:
                continue
            in_comment = False
            # A heading after a comment terminator on the same line is not
            # a standalone Markdown heading.
            continue
        line, marker, rest = raw_line.partition("<!--")
        if marker and "-->" not in rest:
            in_comment = True
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if opening and (opening[1][0] == "~" or "`" not in opening[2]):
            fence = opening[1]
            continue
        if content_tag.match(line):
            raw_html = content_end.search(line) is None
            continue
        if re.match(r"^ {0,3}<(?:/?[A-Za-z]|[!?])", line):
            # Other raw HTML blocks end at a blank line; conservatively skip
            # unknown tags rather than accepting a hidden version heading.
            html_until_blank = True
            continue
        if heading.match(line):
            return True
    return False


def validate_version_contract(profile: dict[str, Any], root: Path) -> str | None:
    if profile["schema"] == "project-profile/v2":
        # v2 did not declare a reader, value path, history source or mirrors.
        # Check the local file safely without claiming its version was parsed.
        version_source_file(root, profile["versioning"]["canonical_source"], "canonical version")
        return None
    source, mirrors, history_source, history_format = _version_contract(profile)
    version = version_value(root, source)
    for mirror in mirrors:
        require(version_value(root, mirror, "version mirror") == version,
                "Canonical version and mirror diverge: " + mirror["path"])
    history = version_source_file(root, history_source, "canonical version history")
    require(history_format == "markdown-headings", "Unsupported canonical history reader")
    require(history.stat().st_size <= 2 * 1024 * 1024, "Canonical version history is too large")
    token = re.escape(version)
    heading = re.compile(r"^##[ \t]+(?:\[v?" + token + r"\]|v?" + token + r")(?=[ \t]|$)")
    require(_history_has_heading(history.read_text(encoding="utf-8"), heading),
            "Canonical history has no entry for integrated version " + version)
    return version


def reject_tracked_local_overrides(root: Path) -> None:
    """A checkout cannot supply a machine-local choice from its Git index."""
    root = root.resolve()
    if not (root / ".git").exists():
        return
    paths = (".local/config/execution-profile.json", ".local/config/preset.json")
    try:
        result = subprocess.run(
            ["git", "--literal-pathspecs", "ls-files", "--cached", "-z", "--", *paths],
            cwd=root, capture_output=True, check=True, timeout=10,
            env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")})
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        raise ValueError("Cannot verify Git tracking for machine-local configuration") from error
    tracked = set(result.stdout.split(b"\0"))
    for path in paths:
        require(path.encode("ascii") not in tracked,
                "Tracked machine-local configuration is invalid: " + path)


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
        reject_tracked_local_overrides(root)
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
            selected_skills = profile.get("skills", [])
            require(len(selected_skills) == len(set(selected_skills)), "Duplicate selected skill name")
            for skill in selected_skills:
                require(re.fullmatch(r"[a-z0-9-]+", skill) is not None, "Invalid selected skill name")
                project_file(root, f"{skills}/{skill}/SKILL.md", "selected executor skill")
            skill_root = root / skills
            if (skill_root.exists() or skill_root.is_symlink() or
                    getattr(skill_root, "is_junction", lambda: False)()):
                require(skill_root.is_dir() and not skill_root.is_symlink() and
                        not getattr(skill_root, "is_junction", lambda: False)(),
                        "Unsafe enabled executor skill root: " + skills)
                actual = set()
                for child in skill_root.iterdir():
                    require(child.is_dir() and not child.is_symlink() and
                            not getattr(child, "is_junction", lambda: False)() and
                            re.fullmatch(r"[a-z0-9-]+", child.name) is not None,
                            "Unexpected executor skill-root entry: " + child.relative_to(root).as_posix())
                    actual.add(child.name)
                require(actual == set(selected_skills),
                        "Enabled executor skills differ from profile.skills: " + skills)
        if profile["schema"] == "project-profile/v3":
            disabled_paths = {
                "codex": ("AGENTS.md", ".agents/skills", ".codex"),
                "claude_code": ("CLAUDE.md", ".claude", ".mcp.json"),
            }
            selected = set(profile["workflow"]["implementation_harnesses"])
            def present(relative: str) -> bool:
                path = root / relative
                return path.exists() or path.is_symlink() or getattr(path, "is_junction", lambda: False)()
            for harness, paths in disabled_paths.items():
                if harness in selected:
                    continue
                for relative in paths:
                    require(not present(relative), "Disabled executor artifact remains: " + relative)
            # Neither local Claude overrides nor project MCP servers are declared
            # by v3, even when Claude itself is selected.
            for relative in (".claude/settings.local.json", ".mcp.json"):
                require(not present(relative), "Unselected project-local configuration remains: " + relative)


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
