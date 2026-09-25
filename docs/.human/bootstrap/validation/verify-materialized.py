"""Read-only structural verification of a materialized downstream project.

Run from a retained copy of the bootstrap tools. Product behavior is a separate gate.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

from validation_core import (inventory, load_json, materialized_profile, profile_schema,
                             schema_check, secret_findings, sensitive_name)

TEXT_SUFFIXES = {".md", ".json", ".toml", ".yml", ".yaml", ".txt", ".py", ".js", ".cjs", ".html", ".css"}
SCHEMAS = Path(__file__).resolve().parents[4] / "docs/.ai/schemas"
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_INVENTORY_FILES = 10_000
MAX_INVENTORY_BYTES = 512 * 1024 * 1024


class BlockedCheck(RuntimeError):
    pass


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.values.append(values["src"])
        if tag == "link" and values.get("href"):
            self.values.append(values["href"])


def inspect(root: Path) -> list[dict]:
    root = root.resolve()
    results = []

    def check(check_id: str, action, evidence: str) -> None:
        try:
            detail = action()
            status, summary = "pass", detail or "Verified in the requested checkout"
        except BlockedCheck as error:
            status, summary = "blocked", str(error)
        except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
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
        if data["schema"] == "project-profile/v3" and data["console"]["enabled"]:
            console = root / "project-console"
            for name in ("index.html", "styles.css", "preset.js", "execution-profile.js", "console.js"):
                require((console / name).is_file() and not (console / name).is_symlink(),
                        "selected Project Console dependency missing: " + name)
            parser = LocalReferences()
            parser.feed((console / "index.html").read_text(encoding="utf-8"))
            for reference in parser.values:
                parsed = urlsplit(reference)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (console / parsed.path).resolve()
                require(target.is_relative_to(console.resolve()) and target.is_file(),
                        "selected Project Console reference missing: " + reference)

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
