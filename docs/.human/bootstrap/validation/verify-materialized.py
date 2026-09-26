"""Read-only structural verification of a materialized downstream project.

Run from a retained copy of the bootstrap tools. Product behavior is a separate gate.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import unquote, urlsplit

from validation_core import (inventory, load_json, materialized_profile, profile_schema,
                             schema_check, secret_findings, sensitive_name)

TEXT_SUFFIXES = {".md", ".json", ".toml", ".yml", ".yaml", ".txt", ".py", ".js", ".cjs", ".html", ".css"}
SCHEMAS = Path(__file__).resolve().parents[4] / "docs/.ai/schemas"
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_INVENTORY_FILES = 10_000
MAX_INVENTORY_BYTES = 512 * 1024 * 1024
CSS_URL = re.compile(r"url\s*\(\s*(?P<quote>['\"]?)(?P<reference>.*?)(?P=quote)\s*\)", re.I | re.S)
CSS_IMPORT = re.compile(r"@import\b", re.I)
CSS_QUOTED = re.compile(r"(?P<quote>['\"])(?P<reference>.*?)(?P=quote)", re.S)


class BlockedCheck(RuntimeError):
    pass


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources = []
        self.inline_styles = []
        self.in_style = False
        self.has_base = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "base":
            self.has_base = True
        if tag == "script" and "src" in values:
            self.resources.append((values["src"], False))
        if tag == "link" and "href" in values:
            stylesheet = "stylesheet" in (values.get("rel") or "").lower().split()
            self.resources.append((values["href"], stylesheet))
        if tag == "style":
            self.in_style = True
        if "style" in values:
            self.inline_styles.append(values["style"] or "")

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.inline_styles.append(data)


def local_console_resource(reference: str, base: Path, console: Path) -> Path:
    """Resolve only relative files within the selected local Console."""
    if (not isinstance(reference, str) or not reference or reference != reference.strip()
            or "\\" in reference or any(ord(char) < 32 or ord(char) == 127 for char in reference)):
        raise ValueError("selected Project Console invalid local reference: " + str(reference))
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc:
        raise ValueError("selected Project Console non-local reference: " + reference)
    path = unquote(parsed.path)
    if not path or path.startswith("/") or Path(path).is_absolute():
        raise ValueError("selected Project Console reference must be relative: " + reference)
    target = (base / path).resolve()
    if not target.is_relative_to(console.resolve()):
        raise ValueError("selected Project Console reference escapes project-console: " + reference)
    if not target.is_file():
        raise ValueError("selected Project Console reference missing: " + reference)
    return target


def css_references(content: str) -> list[str]:
    """Extract simple CSS imports and URLs; reject syntax this offline check cannot prove local."""
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.S)
    if "\\" in content:
        raise ValueError("selected Project Console CSS escapes are unsupported in the local resource check")
    references = [match.group("reference") for match in CSS_URL.finditer(content)]
    for match in CSS_IMPORT.finditer(content):
        remainder = content[match.end():].lstrip()
        quoted = CSS_QUOTED.match(remainder)
        if quoted:
            references.append(quoted.group("reference"))
        elif not CSS_URL.match(remainder):
            raise ValueError("selected Project Console CSS import cannot be verified as local")
    return references


def inspect(root: Path) -> list[dict]:
    root = root.resolve()
    results = []

    def check(check_id: str, action, evidence: str) -> None:
        try:
            detail = action()
            status, summary = "pass", detail or "Verified in the requested checkout"
        except BlockedCheck as error:
            status, summary = "blocked", str(error)
        except (ValueError, OSError, KeyError, TypeError, RuntimeError, UnicodeError) as error:
            status, summary = "fail", str(error)
        results.append({"check_id": check_id, "scope": "structure", "required": True,
                        "status": status, "evidence_ref": evidence, "summary": summary})

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)

    def profile() -> None:
        path = root / "docs/.ai/project-profile.json"
        require(path.is_file() and not path.is_symlink(), "project profile missing")
        data = load_json(path)
        schema_check(profile_schema(SCHEMAS, data), data)
        materialized_profile(data, root)
        if data["schema"] == "project-profile/v3":
            # v3 declares a protected manual default. Check the selected native files,
            # because their existence alone does not prove that default is in force.
            for harness in data["workflow"]["implementation_harnesses"]:
                if harness == "codex":
                    native = root / ".codex/config.toml"
                    require(native.stat().st_size <= MAX_TEXT_BYTES, "Enabled Codex configuration is too large")
                    settings = tomllib.loads(native.read_text(encoding="utf-8"))
                    require(settings.get("sandbox_mode") == "workspace-write" and
                            settings.get("approval_policy") == "on-request" and
                            settings.get("approvals_reviewer") == "user",
                            "Enabled Codex protected manual defaults are not configured")
                elif harness == "claude_code":
                    native = root / ".claude/settings.json"
                    require(native.stat().st_size <= MAX_TEXT_BYTES, "Enabled Claude configuration is too large")
                    settings = load_json(native)
                    permissions = settings.get("permissions") if isinstance(settings, dict) else None
                    sandbox = settings.get("sandbox") if isinstance(settings, dict) else None
                    require(isinstance(permissions, dict) and permissions.get("defaultMode") == "default" and
                            isinstance(sandbox, dict) and sandbox.get("enabled") is True,
                            "Enabled Claude protected manual defaults are not configured")
        if data["schema"] == "project-profile/v3" and data["console"]["enabled"]:
            console = root / "project-console"
            require(console.is_dir() and not console.is_symlink(), "selected Project Console directory missing or linked")
            for name in ("index.html", "styles.css", "preset.js", "execution-profile.js", "console.js"):
                require((console / name).is_file() and not (console / name).is_symlink(),
                        "selected Project Console dependency missing: " + name)
            parser = LocalReferences()
            parser.feed((console / "index.html").read_text(encoding="utf-8"))
            require(not parser.has_base, "selected Project Console base URL is unsupported")
            stylesheets = [console / "styles.css"]
            for reference, stylesheet in parser.resources:
                target = local_console_resource(reference, console, console)
                if stylesheet or target.suffix.lower() == ".css":
                    stylesheets.append(target)
            for content in parser.inline_styles:
                for reference in css_references(content):
                    target = local_console_resource(reference, console, console)
                    if target.suffix.lower() == ".css":
                        stylesheets.append(target)
            seen = set()
            while stylesheets:
                stylesheet = stylesheets.pop()
                if stylesheet in seen:
                    continue
                seen.add(stylesheet)
                require(stylesheet.stat().st_size <= MAX_TEXT_BYTES,
                        "selected Project Console CSS exceeds local resource check limit: " + str(stylesheet))
                for reference in css_references(stylesheet.read_text(encoding="utf-8")):
                    target = local_console_resource(reference, stylesheet.parent, console)
                    if target.suffix.lower() == ".css":
                        stylesheets.append(target)

    def pruning() -> None:
        require(not (root / "docs/.human/bootstrap").exists(), "bootstrap directory remains")
        require(not (root / ".github/workflows/bootcrate-validate.yml").exists(), "bootstrap workflow remains")
        readme = root / "README.md"
        if readme.is_file():
            require("This package is **BootCrate v" not in readme.read_text(encoding="utf-8"),
                    "README still carries BootCrate package identity")

    cached = None

    def candidates():
        nonlocal cached
        if cached is not None:
            return cached
        tracked, untracked = inventory(root)
        paths = sorted(set(tracked + untracked))
        require(len(paths) <= MAX_INVENTORY_FILES,
                f"inventory exceeds {MAX_INVENTORY_FILES} files")
        total = 0
        tracked_set = set(tracked)
        for path in paths:
            rel = path.relative_to(root)
            require(not path.is_symlink() and path.resolve().is_relative_to(root),
                    "symlink/external path: " + str(rel))
            if path.is_dir():
                raise BlockedCheck("submodule/directory inventory requires a selected verifier: " + str(rel))
            require(path.is_file(), "inventory path is not a regular file: " + str(rel))
            require(path not in tracked_set or not sensitive_name(path),
                    "secret-bearing filename tracked: " + str(rel))
            total += path.stat().st_size
            require(total <= MAX_INVENTORY_BYTES,
                    f"inventory exceeds {MAX_INVENTORY_BYTES} bytes")
        cached = tracked_set, paths, total
        return cached

    def files() -> str:
        _, paths, total = candidates()
        return f"Inventoried {len(paths)} files / {total} bytes without following links"

    def text_scan() -> str:
        _, paths, _ = candidates()
        scanned = 0
        oversized = []
        for path in paths:
            rel = path.relative_to(root)
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.stat().st_size > MAX_TEXT_BYTES:
                oversized.append(str(rel))
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as error:
                raise BlockedCheck("text candidate is not UTF-8 and was not scanned: " + str(rel)) from error
            scanned += 1
            require("docs/.human/bootstrap/" not in content, "dangling bootstrap reference: " + str(rel))
            require(not secret_findings(content), "secret-pattern smoke check failed: " + str(rel))
        if oversized:
            raise BlockedCheck("text scan limit exceeded: " + ", ".join(oversized[:5]))
        return f"Scanned {scanned} bounded UTF-8 text candidates; binary assets were metadata-only"

    check("profile.finalized", profile, "docs/.ai/project-profile.json")
    check("bootstrap.pruned", pruning, "PROJECT_GUIDE.md + bootstrap absence")
    check("source.inventory", files, "git ls-files or bounded project inventory")
    check("security.text_scan", text_scan, "bounded UTF-8 candidates from source inventory")
    results.append({"check_id": "behavior.native", "scope": "behavior", "required": False,
                    "status": "not_run", "evidence_ref": "native project checks",
                    "summary": "Run applicable build/test/smoke/security checks separately; structure cannot prove behavior"})
    return results


def check(root: Path) -> list[str]:
    """Backward-compatible list of failures for callers expecting the earlier smoke API."""
    return [entry["summary"] for entry in inspect(root)
            if entry["required"] and entry["status"] != "pass"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit structured check results")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error("downstream root is not a directory")
    try:
        results = inspect(args.root)
    except (OSError, RuntimeError) as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"checks": results}, ensure_ascii=False, indent=2))
    else:
        for entry in results:
            print(entry["status"].upper() + ": " + entry["check_id"] + " — " + entry["summary"])
    return 1 if any(e["required"] and e["status"] != "pass" for e in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
