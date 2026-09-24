"""Offline structural validation of BootCrate; no model calls or production access."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from typing import Any

from validation_core import (require, unique_object, load_json, inventory as project_inventory,
                             sensitive_name, secret_findings, local_refs_only, schema_check,
                             materialized_profile, profile_schema)

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit("Install bootstrap validation/requirements.txt in an isolated Python environment.")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BOOT = ROOT / "docs/.human/bootstrap"
SKIP = {".git", ".local", ".venv", "__pycache__", "node_modules", ".temp"}
EXAMPLES = {".env.example", ".env.sample", ".env.template"}


class UniqueLoader(yaml.SafeLoader):
    """Safe YAML with duplicate rejection and YAML-1.2-style boolean spellings."""


UniqueLoader.yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for key, entries in UniqueLoader.yaml_implicit_resolvers.items():
    UniqueLoader.yaml_implicit_resolvers[key] = [e for e in entries if e[0] != "tag:yaml.org,2002:bool"]
UniqueLoader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false|True|False|TRUE|FALSE)$"), list("tTfF"))


def unique_mapping(loader: UniqueLoader, node: Any, deep: bool = False) -> dict[str, Any]:
    loader.flatten_mapping(node)
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        require(key not in result, f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_yaml(text: str) -> Any:
    return yaml.load(text, Loader=UniqueLoader)


def run(command: list[str], cwd: Path = ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=90)
    require(result.returncode == 0, f"Command failed: {' '.join(command)}\n{result.stderr[:2000]}")
    return result.stdout + result.stderr


def question_data() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = (BOOT / "app/questions.js").read_text(encoding="utf-8")
    match = re.fullmatch(r"\s*window\.BOOTCRATE_QUESTIONS\s*=\s*(\[.*?\]);\s*window\.BOOTCRATE_SECTIONS\s*=\s*(\{.*\});\s*", source, re.S)
    require(match is not None, "Question file must remain a data-only assignment")
    return json.loads(match[1]), json.loads(match[2])


def check_questions() -> None:
    questions, sections = question_data()
    by_id = {q["id"]: q for q in questions}
    require(len(by_id) == len(questions), "Duplicate question ids")
    intake = load_json(BOOT / "schemas/project-intake.schema.json")["properties"]
    schema = intake["answers"]["properties"]
    require(set(schema) == set(by_id), "Question/schema IDs diverged")
    state_ids = {q["id"] for q in questions if not q.get("required") and q["type"] in {"text", "textarea"}}
    require(set(intake["answer_states"]["properties"]) == state_ids,
            "Explicit unknown/not-applicable fields diverged")
    for q in questions:
        require(q["section"] in sections and q.get("en") and q.get("pt"), "Question section/translation missing")
        spec = schema[q["id"]]
        expected = "array" if q["type"] == "multiselect" else "string"
        require(spec["type"] == expected, "Question/schema type mismatch: " + q["id"])
        if "options" in q:
            options = [o[0] for o in q["options"]]
            require(len(options) == len(set(options)), "Duplicate option")
            actual = spec["items"]["enum"] if expected == "array" else spec["enum"]
            require(options == actual, "Question/schema choices diverged: " + q["id"])
        visited = {q["id"]}
        current = q
        while "condition" in current:
            parent = current["condition"]["id"]
            require(parent in by_id and parent not in visited, "Invalid/cyclic condition")
            options = {o[0] for o in by_id[parent].get("options", [])}
            require(set(current["condition"]["in"]) <= options, "Condition references unknown choice")
            visited.add(parent)
            current = by_id[parent]


def check_documents(files: list[Path]) -> None:
    for path in files:
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^\s)]+)\)", text):
                if "://" in target or target.startswith(("#", "mailto:")) or "<" in target:
                    continue
                require((path.parent / target.split("#")[0]).exists(), f"Broken relative link: {path.relative_to(ROOT)} -> {target}")
    policy = (ROOT / "docs/.ai/TASK_POLICY.md").read_text(encoding="utf-8")
    require(all(x in policy for x in ["Medium eligibility", "High", "XHigh", "Target Version", "Continuations"]), "Task invariants missing")
    prompt = (ROOT / "docs/.ai/prompts/base.md").read_text(encoding="utf-8")
    require("# [<TARGET_VERSION>]" in prompt and "Security:" in prompt, "Base prompt lost identity/security")
    materializer = (BOOT / "templates/bootstrap-materialization.md").read_text(encoding="utf-8")
    require("SECURITY_BASELINE" in materializer and "bootcrate-validate.yml" in materializer, "Materialization lost security/pruning contract")
    version = (ROOT / "VERSION").read_text().strip()
    require(re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version) is not None, "Invalid VERSION")
    require(f"BootCrate v{version}" in (ROOT / "README.md").read_text(encoding="utf-8"), "README/version mismatch")
    guide = (ROOT / "PROJECT_GUIDE.md").read_text(encoding="utf-8")
    require("stable entry point" in guide and "active work state" in guide, "PROJECT_GUIDE lost stable routing/authority")
    project_instructions = (BOOT / "templates/chatgpt-project-instructions.md").read_text(encoding="utf-8")
    require("PROJECT_GUIDE.md" in project_instructions, "ChatGPT Project instructions must route through PROJECT_GUIDE")
    require("docs/.ai/TASK_POLICY.md" not in project_instructions and "AGENTS.md / CLAUDE.md" not in project_instructions,
            "ChatGPT Project instructions leaked mutable internal routes")
    require("PROJECT_GUIDE.md" in materializer and "Preserve" in materializer, "Materialization must preserve PROJECT_GUIDE")


def check_adapters() -> None:
    codex = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    require(codex["model_reasoning_effort"] == "high", "Main default must remain High")
    require(codex["approval_policy"] == "on-request" and codex["sandbox_mode"] == "workspace-write", "Unsafe Codex defaults")
    require(codex["sandbox_workspace_write"]["network_access"] is False, "Sandbox network widened")
    require(codex["agents"]["max_concurrent_threads_per_session"] <= 2, "Agent concurrency widened")
    require(codex["shell_environment_policy"]["inherit"] == "core", "Unexpected credential environment inheritance")
    scout = tomllib.loads((ROOT / ".codex/agents/scout.toml").read_text(encoding="utf-8"))
    require(scout["sandbox_mode"] == "read-only", "Codex Scout may write")
    text = (ROOT / ".claude/agents/scout.md").read_text(encoding="utf-8")
    fm = load_yaml(text.split("---", 2)[1])
    require(set(t.strip() for t in fm["tools"].split(",")) == {"Read", "Grep", "Glob"}, "Claude Scout tool pool widened")
    settings = load_json(ROOT / ".claude/settings.json")
    require(settings["effortLevel"] == "high" and settings["permissions"]["defaultMode"] == "default", "Unsafe Claude defaults")
    require(settings.get("sandbox", {}).get("enabled") is True, "Claude sandbox baseline disabled")
    require("Read(./**/.env)" in settings["permissions"]["deny"], "Nested env denial missing")
    for canonical in (BOOT / "library/skills").glob("*/SKILL.md"):
        relative = canonical.relative_to(BOOT / "library/skills")
        content = canonical.read_text(encoding="utf-8")
        require(content.startswith("---\n") and "\n---\n" in content[4:], "Invalid skill frontmatter")
        frontmatter = load_yaml(content.split("---", 2)[1])
        require(frontmatter.get("name") == canonical.parent.name and bool(frontmatter.get("description")) and
                len(content.splitlines()) < 500, "Invalid skill name, description or length")
        for target in [ROOT / ".agents/skills", ROOT / ".claude/skills"]:
            require(canonical.read_bytes() == (target / relative).read_bytes(), "Skill semantic source drift: " + str(relative))
    adapters = [load_json(path) for path in (BOOT / "library/adapters").glob("*.json")]
    require({a["id"] for a in adapters} == {"codex", "claude_code"}, "Unsupported/missing executor adapter")
    for adapter in adapters:
        require(adapter["schema"] == "bootcrate-adapter/v1" and
                adapter["declared"]["main_requested"] == ["medium", "high", "xhigh"] and
                adapter["declared"]["consumption_presets"] == ["standard", "economy"],
                "Adapter weakens common effort/preset contract")
    require((BOOT / "app/preset.js").read_bytes() == (BOOT / "console/preset.js").read_bytes(),
            "Setup/Console preset resolver drift")


def check_github() -> None:
    labels = load_yaml((ROOT / ".github/labels.yml").read_text(encoding="utf-8"))
    names = {x["name"] for x in labels}
    require(len(names) == len(labels), "Duplicate label")
    for label in labels:
        require(re.fullmatch(r"[0-9a-fA-F]{6}", label["color"]) is not None, "Invalid label color")
    for path in (ROOT / ".github/ISSUE_TEMPLATE").glob("*.yml"):
        if path.name == "config.yml": continue
        form = load_yaml(path.read_text(encoding="utf-8"))
        require(set(form.get("labels", [])) <= names, "Form references absent desired label")
        ids = [x["id"] for x in form["body"] if "id" in x]
        require(len(ids) == len(set(ids)), "Duplicate form input id")
    workflow = load_yaml((ROOT / ".github/workflows/bootcrate-validate.yml").read_text(encoding="utf-8"))
    require(workflow["permissions"] == {"contents": "read"}, "Workflow permissions widened")
    require(set(workflow["on"]) == {"push", "pull_request", "workflow_dispatch"}, "Unsafe/unexpected workflow trigger")
    for job in workflow["jobs"].values():
        require(job.get("timeout-minutes", 999) <= 15, "Unbounded CI job")
        for step in job["steps"]:
            if "uses" in step:
                require(re.fullmatch(r"[^@]+@[0-9a-f]{40}", step["uses"]) is not None, "Unpinned external action")


def check_ignore() -> None:
    if not (ROOT / ".git").exists():
        require(".env" in (ROOT / ".gitignore").read_text(), "Missing secret ignore rules")
        return
    for name in [".env", "nested/.env.production", "nested/secrets.json", ".local/config/project.json", "private.key"]:
        result = subprocess.run(["git", "check-ignore", "--no-index", "--quiet", name], cwd=ROOT)
        require(result.returncode == 0, "Path is not ignored: " + name)
    for name in [".env.example", "nested/.env.template", "src/example.py"]:
        result = subprocess.run(["git", "check-ignore", "--no-index", "--quiet", name], cwd=ROOT)
        require(result.returncode == 1, "Safe example/source incorrectly ignored: " + name)


def validate() -> None:
    tracked, untracked = project_inventory(ROOT)
    files = sorted(set(tracked + untracked))
    for path in files:
        rel = path.relative_to(ROOT)
        require(not path.is_symlink() and path.resolve().is_relative_to(ROOT.resolve()), "Unexpected symlink/external path: " + str(rel))
        require(not (set(rel.parts) & {".local", ".venv"}), "Local state is tracked")
        require(not sensitive_name(path), "Secret-bearing filename is tracked: " + str(rel))
        require(path.stat().st_size < 2 * 1024 * 1024, "Unexpected bulk template file: " + str(rel))
        text = path.read_text(encoding="utf-8")
        require(not secret_findings(text), "Secret-pattern smoke check failed in " + str(rel))
        if path.suffix == ".json": load_json(path)
        if path.suffix in {".yml", ".yaml"}: load_yaml(text)
        if path.suffix == ".toml": tomllib.loads(text)
    profile = load_json(ROOT / "docs/.ai/project-profile.json")
    schema_check(profile_schema(ROOT / "docs/.ai/schemas", profile), profile)
    schema_check(load_json(BOOT / "schemas/project-intake.schema.json"), load_json(BOOT / "templates/project-intake.example.json"))
    check_questions()
    check_documents(files)
    check_adapters()
    check_github()
    check_ignore()
    require(shutil.which("node") is not None, "Node.js 20+ is required for bootstrap intake tests")
    for path in (BOOT / "app").glob("*.js"):
        run(["node", "--check", str(path)])
    print(run(["node", "--test", str(HERE / "test-intake.cjs")]).strip())
    print(run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py", "-v"]).strip())
    print(f"PASS: {len(files)} candidate files; structural/configuration checks and deterministic tests.")
    print("Not performed here: live harness enforcement, model evals, owner projects, browser UX or penetration testing.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialized-profile", type=Path, help="Validate a finalized downstream profile without remote schema fetches")
    args = parser.parse_args()
    try:
        if args.materialized_profile:
            data = load_json(args.materialized_profile)
            schema_check(profile_schema(ROOT / "docs/.ai/schemas", data), data)
            materialized_profile(data, args.materialized_profile.resolve().parents[2])
            print("PASS: finalized profile structure (not a production-security assessment)")
        else:
            validate()
    except yaml.YAMLError:
        print("FAIL: malformed YAML; inspect candidate YAML files locally.", file=sys.stderr)
        raise SystemExit(1)
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, TypeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
