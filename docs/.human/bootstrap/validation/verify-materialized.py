"""Read-only structural verification of a materialized downstream project.

Run from a retained copy of the bootstrap tools. Product behavior is a separate gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from validation_core import (inventory, load_json, materialized_profile, profile_schema,
                             schema_check, secret_findings, sensitive_name)

TEXT_SUFFIXES = {".md", ".json", ".toml", ".yml", ".yaml", ".txt", ".py", ".js", ".cjs", ".html", ".css"}
SCHEMAS = Path(__file__).resolve().parents[4] / "docs/.ai/schemas"


def inspect(root: Path) -> list[dict]:
    root = root.resolve()
    results = []

    def check(check_id: str, action, evidence: str) -> None:
        try:
            action()
            status, summary = "pass", "Verified in the requested checkout"
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
            require((root / "project-console/index.html").is_file(), "selected Project Console missing")

    def pruning() -> None:
        require(not (root / "docs/.human/bootstrap").exists(), "bootstrap directory remains")
        require(not (root / ".github/workflows/bootcrate-validate.yml").exists(), "bootstrap workflow remains")
        readme = root / "README.md"
        if readme.is_file():
            require("This package is **BootCrate v" not in readme.read_text(encoding="utf-8"),
                    "README still carries BootCrate package identity")

    def files() -> None:
        tracked, untracked = inventory(root)
        for path in sorted(set(tracked + untracked)):
            rel = path.relative_to(root)
            require(not path.is_symlink() and path.resolve().is_relative_to(root),
                    "symlink/external path: " + str(rel))
            require(path not in tracked or not sensitive_name(path), "secret-bearing filename tracked: " + str(rel))
            require(path.stat().st_size <= 2 * 1024 * 1024, "oversized candidate file: " + str(rel))
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            require("docs/.human/bootstrap/" not in content, "dangling bootstrap reference: " + str(rel))
            require(not secret_findings(content), "secret-pattern smoke check failed: " + str(rel))

    check("profile.finalized", profile, "docs/.ai/project-profile.json")
    check("bootstrap.pruned", pruning, "PROJECT_GUIDE.md + bootstrap absence")
    check("source.inventory", files, "git ls-files or bounded project inventory")
    results.append({"check_id": "behavior.native", "scope": "behavior", "required": False,
                    "status": "not_run", "evidence_ref": "native project checks",
                    "summary": "Run applicable build/test/smoke/security checks separately; structure cannot prove behavior"})
    return results


def check(root: Path) -> list[str]:
    """Backward-compatible list of failures for callers expecting the earlier smoke API."""
    return [entry["summary"] for entry in inspect(root) if entry["status"] == "fail"]


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
