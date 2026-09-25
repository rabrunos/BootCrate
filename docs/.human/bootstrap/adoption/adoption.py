"""Local Adoption Sandbox: prepare, review and apply a strictly identified delta.

The original is not written by prepare or inspect. Apply writes only the reviewed
patch and never commits, pushes, provisions services or decides acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

META = "bootcrate-adoption.json"


def git(root: Path, *args: str, input: bytes | None = None) -> bytes:
    p = subprocess.run(["git", *args], cwd=root, input=input, capture_output=True, timeout=90)
    if p.returncode:
        raise ValueError("Git operation failed: " + " ".join(args) + " (" + p.stderr.decode(errors="replace")[:300] + ")")
    return p.stdout


def safe_root(root: Path) -> Path:
    root = root.resolve(strict=True)
    if git(root, "rev-parse", "--show-toplevel").decode().strip() != str(root):
        raise ValueError("Select the repository root, not a nested folder")
    return root


def paths(root: Path, *args: str) -> list[str]:
    names = git(root, "ls-files", "-z", *args).split(b"\0")
    return [name.decode("utf-8") for name in names if name]


def state(root: Path) -> dict[str, str]:
    """Record local differences, without reading ignored files or secrets."""
    names = set(paths(root, "--modified")) | set(paths(root, "--deleted")) | set(paths(root, "--others", "--exclude-standard"))
    names |= set(git(root,"diff","--name-only","-z","--cached").decode().strip("\0").split("\0"))
    result = {}
    for name in sorted(names - {""}):
        path = root / name
        if path.is_symlink():
            raise ValueError("Symlink in local changes: " + name)
        if path.exists():
            if not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
                raise ValueError("Unsupported local file in sandbox preparation: " + name)
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            result[name] = "deleted"
    return result


def sha(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").decode().strip()


def meta(sandbox: Path) -> dict:
    return json.loads((sandbox / ".git" / META).read_text(encoding="utf-8"))


def prepare(original: Path, sandbox: Path, include_local_changes: bool = False) -> dict:
    original = safe_root(original)
    sandbox = sandbox.absolute()
    if sandbox.exists():
        raise ValueError("Sandbox destination already exists")
    # Resolve parent links before creating anything; a symlinked parent can point into the original.
    if (sandbox.parent.resolve() / sandbox.name).is_relative_to(original):
        raise ValueError("Sandbox must not be nested inside the original")
    baseline_sha, baseline_state = sha(original), state(original)
    if baseline_state and not include_local_changes:
        raise ValueError("Original contains local changes; review and explicitly select --include-local-changes")
    try:
        git(original, "clone", "--no-local", "--no-hardlinks", str(original), str(sandbox))
        if sha(sandbox) != baseline_sha or sha(original) != baseline_sha:
            raise ValueError("Original HEAD changed during sandbox creation")
        git(sandbox, "remote", "remove", "origin")  # No implicit push target.
        git(sandbox, "config", "push.default", "nothing")
        if baseline_state:
            patch = git(original, "diff", "--binary", "HEAD")
            if patch:
                git(sandbox, "apply", "--binary", "-", input=patch)
            untracked = set(paths(original, "--others", "--exclude-standard"))
            for name in untracked:
                target = sandbox / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original / name, target)
            git(sandbox, "add", "-A")
            git(sandbox, "-c", "user.name=BootCrate Sandbox", "-c", "user.email=sandbox@example.invalid",
                "commit", "-qm", "Snapshot of original local changes for adoption comparison")
        if sha(original) != baseline_sha or state(original) != baseline_state:
            raise ValueError("Original local state changed during sandbox preparation")
        baseline = sha(sandbox)
        info = {"format": 1, "original": str(original), "original_head": baseline_sha,
                "original_local": baseline_state, "sandbox_baseline": baseline}
        (sandbox / ".git" / META).write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        return {"original_head": baseline_sha, "sandbox_baseline": baseline,
                "local_changes_included": len(baseline_state), "remote_push_enabled": False}
    except Exception:
        if sandbox.exists():
            shutil.rmtree(sandbox)
        raise


def inspect(sandbox: Path) -> dict:
    sandbox = safe_root(sandbox)
    info = meta(sandbox)
    base, head = info["sandbox_baseline"], sha(sandbox)
    git(sandbox, "merge-base", "--is-ancestor", base, head)
    changed = git(sandbox, "diff", "--name-status", "-z", base + ".." + head).decode().strip("\0").split("\0")
    # -z format alternates status and path, with two paths for rename/copy.
    if any(status.startswith(("R", "C")) for status in changed[::2]):
        raise ValueError("Review renames/copies manually before Apply Adoption")
    for path in changed[1::2]:
        current = sandbox / path
        if current.is_symlink() or not current.resolve().is_relative_to(sandbox):
            raise ValueError("Unsafe symlink in committed delta: " + path)
    return {"original_head": info["original_head"], "sandbox_baseline": base,
            "approved_head_candidate": head, "changed": list(zip(changed[::2], changed[1::2])),
            "sandbox_local_changes": state(sandbox)}


def apply(sandbox: Path, approved_head: str) -> dict:
    sandbox = safe_root(sandbox)
    info = meta(sandbox)
    original = safe_root(Path(info["original"]))
    report = inspect(sandbox)
    if report["sandbox_local_changes"]:
        raise ValueError("Commit the reviewed sandbox delta before applying")
    if report["approved_head_candidate"] != approved_head:
        raise ValueError("Sandbox HEAD changed after review")
    if sha(original) != info["original_head"] or state(original) != info["original_local"]:
        raise ValueError("Original baseline changed; reconcile before applying")
    affected = [path for _, path in report["changed"]]
    if any((original / path).is_symlink() or not (original / path).resolve().is_relative_to(original)
           for path in affected):
        raise ValueError("Unsafe path in approved delta")
    patch = git(sandbox, "diff", "--binary", info["sandbox_baseline"] + ".." + approved_head)
    if len(patch) > 16 * 1024 * 1024:
        raise ValueError("Approved patch exceeds bounded automatic transfer; review manually")
    if not patch:
        return {"status":"no_changes", "paths":[]}
    git(original, "apply", "--check", "--binary", "-", input=patch)
    if sha(original) != info["original_head"] or state(original) != info["original_local"]:
        raise ValueError("Original changed during preflight")
    git(original, "apply", "--binary", "-", input=patch)
    return {"status":"applied_uncommitted", "paths":affected,
            "next":"Run the same applicable checks in the original; review and commit only after acceptance"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    make = commands.add_parser("prepare")
    make.add_argument("original", type=Path); make.add_argument("sandbox", type=Path)
    make.add_argument("--include-local-changes", action="store_true")
    show = commands.add_parser("inspect"); show.add_argument("sandbox", type=Path)
    move = commands.add_parser("apply"); move.add_argument("sandbox", type=Path)
    move.add_argument("--approved-head", required=True)
    args = p.parse_args()
    try:
        if args.command == "prepare": result = prepare(args.original,args.sandbox,args.include_local_changes)
        elif args.command == "inspect": result = inspect(args.sandbox)
        else: result = apply(args.sandbox,args.approved_head)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__": raise SystemExit(main())
