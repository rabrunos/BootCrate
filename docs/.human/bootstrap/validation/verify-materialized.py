"""Deterministic post-materialization checks for a disposable downstream project."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

TEXT_SUFFIXES={".md",".json",".toml",".yml",".yaml",".txt",".py",".js",".cjs",".html",".css"}

def check(root: Path) -> list[str]:
    errors=[]
    root=root.resolve()
    if (root/"docs/.human/bootstrap").exists(): errors.append("bootstrap directory remains")
    if (root/".github/workflows/bootcrate-validate.yml").exists(): errors.append("bootstrap workflow remains")
    guide=root/"PROJECT_GUIDE.md"
    if not guide.is_file(): errors.append("PROJECT_GUIDE.md missing")
    profile=root/"docs/.ai/project-profile.json"
    if profile.is_file() and "<materialize>" in profile.read_text(encoding="utf-8"): errors.append("project profile still contains materialization placeholders")
    readme=root/"README.md"
    if readme.is_file() and "This package is **BootCrate v" in readme.read_text(encoding="utf-8"): errors.append("README still carries BootCrate package identity")
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts: continue
        rel=path.relative_to(root)
        if any(part in {".local",".venv","node_modules"} for part in rel.parts): continue
        name=path.name.lower()
        if name==".env" or name.startswith((".env.","secrets.","credentials.")) or path.suffix.lower() in {".key",".p12",".pfx"}:
            if name not in {".env.example",".env.sample",".env.template"}: errors.append("secret-bearing filename tracked/present: "+str(rel))
        if path.suffix.lower() in TEXT_SUFFIXES:
            try: text=path.read_text(encoding="utf-8")
            except UnicodeDecodeError: continue
            if "docs/.human/bootstrap/" in text: errors.append("dangling bootstrap reference: "+str(rel))
    return sorted(set(errors))

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    args=parser.parse_args()
    errors=check(args.root)
    for error in errors: print("FAIL:",error)
    if not errors: print("PASS: downstream pruning/profile/guide smoke checks")
    return int(bool(errors))

if __name__=="__main__": raise SystemExit(main())
