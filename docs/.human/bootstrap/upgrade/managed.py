"""Explicit, pre-materialization three-way update of approved managed files.

The manifest is local/ignored and removed with bootstrap. This is not a background
updater for projects after materialization. The lock serializes BootCrate writers;
external writers are detected at write/commit boundaries but cannot be locked by a
portable filesystem API.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import stat
import sys

CONTROL = Path(".local")
MANIFEST = CONTROL / "bootcrate-managed.json"
LOCK = CONTROL / "bootcrate-managed.lock"
MAX_MANAGED_BYTES = 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
_active_mutator = ContextVar("managed_mutator", default=None)


class _PosixMutator:
    """Perform every mutation relative to checked, open directory descriptors."""

    def __init__(self, root: Path):
        required = (os.open, os.mkdir, os.unlink, os.rmdir, os.replace, os.link)
        if not all(operation in os.supports_dir_fd for operation in required):
            raise RuntimeError("Managed update requires directory-relative filesystem operations")
        self.root = root
        self.descriptor = None

    def __enter__(self):
        self.descriptor = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        if not stat.S_ISDIR(os.fstat(self.descriptor).st_mode):
            self.__exit__(None, None, None)
            raise ValueError("Project root is not a real directory")
        return self

    def __exit__(self, *_):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None

    @staticmethod
    def _parts(relative: Path) -> tuple[str, ...]:
        relative = Path(relative)
        if relative.is_absolute() or not relative.parts or any(
            part in ("", ".", "..") for part in relative.parts
        ):
            raise ValueError("Unsafe managed mutation path")
        return relative.parts

    @contextmanager
    def _parent(self, relative: Path):
        parts = self._parts(relative)
        descriptor = os.dup(self.descriptor)
        try:
            for part in parts[:-1]:
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=descriptor,
                )
                os.close(descriptor)
                descriptor = child
            yield descriptor, parts[-1]
        finally:
            os.close(descriptor)

    def write_new(self, relative: Path, data: bytes) -> None:
        with self._parent(relative) as (parent, name):
            descriptor = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600, dir_fd=parent,
            )
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())

    def read(self, relative: Path) -> bytes:
        with self._parent(relative) as (parent, name):
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
            with os.fdopen(descriptor, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError("Managed control file is not regular")
                data = stream.read(4 * 1024 * 1024 + 1)
                if len(data) > 4 * 1024 * 1024:
                    raise ValueError("Managed control file exceeds its read limit")
                return data

    def replace(self, source: Path, target: Path, *, expected_digest: str) -> None:
        if hash_bytes(self.read(source)) != expected_digest:
            raise ValueError("Frozen staged bytes changed before replace")
        with self._parent(source) as (source_parent, source_name):
            with self._parent(target) as (target_parent, target_name):
                os.replace(
                    source_name, target_name,
                    src_dir_fd=source_parent, dst_dir_fd=target_parent,
                )

    def unlink(self, relative: Path, *, missing_ok: bool = False) -> None:
        with self._parent(relative) as (parent, name):
            try:
                os.unlink(name, dir_fd=parent)
            except FileNotFoundError:
                if not missing_ok:
                    raise

    def mkdir(self, relative: Path) -> None:
        with self._parent(relative) as (parent, name):
            os.mkdir(name, dir_fd=parent)

    def rmdir(self, relative: Path) -> None:
        with self._parent(relative) as (parent, name):
            os.rmdir(name, dir_fd=parent)

    def link(self, source: Path, target: Path, *, expected_digest: str) -> None:
        if hash_bytes(self.read(source)) != expected_digest:
            raise ValueError("Frozen staged bytes changed before link")
        with self._parent(source) as (source_parent, source_name):
            with self._parent(target) as (target_parent, target_name):
                os.link(
                    source_name, target_name,
                    src_dir_fd=source_parent, dst_dir_fd=target_parent,
                    follow_symlinks=False,
                )


def _mutator_for(root: Path):
    if os.name != "nt":
        return _PosixMutator(root)
    module_path = Path(__file__).with_name("_windows_mutation.py")
    spec = importlib.util.spec_from_file_location("_bootcrate_windows_mutation", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Windows managed mutation capability is unavailable")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (OSError, AttributeError) as error:
        raise RuntimeError("Windows managed update requires native handle-relative filesystem capability") from error
    return module.WindowsMutator(root)


def _mutator():
    active = _active_mutator.get()
    if active is None:
        raise RuntimeError("Managed mutation requires an anchored filesystem session")
    return active


def _relative(path: Path) -> Path:
    return Path(path).relative_to(_mutator().root)


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _is_link_or_reparse(path: Path) -> bool:
    if not _lexists(path):
        return False
    info = os.lstat(path)
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def validated_root(root: Path) -> Path:
    root = Path(os.path.abspath(root))
    if not root.is_dir() or _is_link_or_reparse(root):
        raise ValueError("Project root must be a real directory, not a link or reparse point")
    if root.resolve(strict=True) != root:
        raise ValueError("Project root resolves through an alias")
    return root


def _safe_child(root: Path, relative: Path, *, control: bool = False) -> Path:
    root = validated_root(root)
    if relative.is_absolute() or relative == Path(".") or not relative.parts:
        raise ValueError("Unsafe path")
    forbidden = {".git"} if control else {".git", ".local"}
    if any(part in {"", ".", ".."} or part in forbidden for part in relative.parts):
        raise ValueError("Unsafe path")
    current = root
    for part in relative.parts:
        current /= part
        if _is_link_or_reparse(current):
            raise ValueError("Link or reparse point in path: " + relative.as_posix())
        if _lexists(current) and current.resolve(strict=True) != current:
            raise ValueError("Path alias escapes the selected root: " + relative.as_posix())
    if not current.absolute().is_relative_to(root):
        raise ValueError("Path escapes root")
    return current


def resolve(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Invalid managed path")
    try:
        return _safe_child(root, Path(relative))
    except ValueError as error:
        raise ValueError("Unsafe managed path: " + relative) from error


def _control_path(root: Path, relative: Path) -> Path:
    if not relative.parts or relative.parts[0] != CONTROL.name:
        raise ValueError("Invalid control path")
    return _safe_child(root, relative, control=True)


def _control_dir(root: Path) -> Path:
    root = validated_root(root)
    path = _control_path(root, CONTROL)
    if _lexists(path):
        if not path.is_dir():
            raise ValueError("BootCrate control path is not a directory")
    else:
        try:
            _mutator().mkdir(CONTROL)
        except FileExistsError:
            pass
    path = _control_path(root, CONTROL)
    if not path.is_dir():
        raise ValueError("BootCrate control directory was replaced during preparation")
    return path


def _strict_json(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate key in manifest: " + key)
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Manifest is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("Manifest must be an object")
    return value


def _read_manifest(root: Path) -> tuple[dict, bytes]:
    bootstrap(root)
    path = _control_path(root, MANIFEST)
    if not path.is_file() or path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest is missing or exceeds its size limit")
    raw = path.read_bytes()
    manifest = _strict_json(raw)
    if (
        manifest.get("schema") != "bootcrate-managed/v1"
        or not isinstance(manifest.get("files"), dict)
        or not isinstance(manifest.get("source_revision"), str)
        or not manifest["source_revision"]
    ):
        raise ValueError("Unsupported or invalid manifest")
    for name, value in manifest["files"].items():
        resolve(root, name)
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError("Invalid base digest")
    return manifest, raw


@contextmanager
def _locked(root: Path):
    with _mutator_for(root) as filesystem:
        filesystem.created = set()
        filesystem.frozen = {}
        marker = _active_mutator.set(filesystem)
        try:
            control = _control_dir(root)
            token = (secrets.token_hex(24) + "\n").encode("ascii")
            try:
                _write_file(_control_path(root, LOCK), token)
            except FileExistsError as error:
                raise ValueError("Another managed update or unrecovered lock is present") from error
            try:
                yield control
            finally:
                current = None
                try:
                    current = filesystem.read(LOCK)
                except (OSError, ValueError):
                    pass
                if current == token:
                    _unlink_file(_control_path(root, LOCK))
                else:
                    raise RuntimeError("Managed-update lock changed; it was preserved for reconciliation")
        finally:
            _active_mutator.reset(marker)


def content(root: Path, relative: str) -> bytes | None:
    path = resolve(root, relative)
    if not _lexists(path):
        return None
    if not path.is_file() or path.stat().st_size > MAX_MANAGED_BYTES:
        raise ValueError("Unsupported managed file: " + relative)
    return path.read_bytes()


def bootstrap(root: Path) -> None:
    root = validated_root(root)
    path = resolve(root, "docs/.human/bootstrap")
    if not path.is_dir():
        raise ValueError("Bootstrap has been pruned: do not recreate a manifest for the product")


def _write_file(path: Path, data: bytes) -> None:
    relative = _relative(path)
    active = _mutator()
    active.write_new(relative, data)
    active.created.add(relative)
    active.frozen[relative] = hash_bytes(data)


def _manifest_bytes(manifest: dict) -> bytes:
    return (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _replace_file(staged: Path, target: Path) -> None:
    """Small patch boundary used by deterministic interleaving tests."""
    source_relative, target_relative = _relative(staged), _relative(target)
    active = _mutator()
    expected_digest = active.frozen.get(source_relative)
    if expected_digest is None:
        raise RuntimeError("Replace source is not a frozen staged file")
    active.replace(source_relative, target_relative, expected_digest=expected_digest)
    active.created.discard(source_relative)
    active.frozen.pop(source_relative)
    active.created.add(target_relative)


def _unlink_file(target: Path, *, missing_ok: bool = False) -> None:
    relative = _relative(target)
    active = _mutator()
    active.unlink(relative, missing_ok=missing_ok)
    active.created.discard(relative)
    active.frozen.pop(relative, None)


def _cleanup_transaction(transaction: Path) -> None:
    relative = _relative(transaction)
    active = _mutator()
    for entry in sorted(active.created, key=lambda item: item.as_posix(), reverse=True):
        if entry.parent == relative:
            active.unlink(entry, missing_ok=True)
            active.created.discard(entry)
            active.frozen.pop(entry, None)
    active.rmdir(relative)


def create(root: Path, revision: str, paths: list[str]) -> dict:
    root = validated_root(root)
    bootstrap(root)
    if not isinstance(revision, str) or not revision:
        raise ValueError("Source revision is required")
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Supply distinct explicitly approved paths")
    files = {}
    for path in paths:
        data = content(root, path)
        if data is None:
            raise ValueError("Managed source missing: " + path)
        files[path] = hash_bytes(data)
    manifest = {"schema": "bootcrate-managed/v1", "source_revision": revision, "files": files}
    raw = _manifest_bytes(manifest)
    with _locked(root) as control:
        target = _control_path(root, MANIFEST)
        if _lexists(target):
            raise ValueError("Manifest already exists")
        staged = control / ("manifest-create-" + secrets.token_hex(12))
        _write_file(staged, raw)
        try:
            # A hard-link publishes the fully written bytes without replacing a concurrent file.
            source_relative = _relative(staged)
            _mutator().link(
                source_relative, _relative(target),
                expected_digest=_mutator().frozen[source_relative],
            )
            if target.read_bytes() != raw:
                raise RuntimeError("Manifest create could not be verified")
        finally:
            _unlink_file(staged, missing_ok=True)
    return manifest


def read(root: Path) -> dict:
    return _read_manifest(validated_root(root))[0]


def _build_plan(root: Path, source: Path, manifest: dict, new_paths: list[str]):
    if len(new_paths) != len(set(new_paths)):
        raise ValueError("Duplicate new path")
    actions, current_bytes, desired_bytes = [], {}, {}
    for name in sorted(set(manifest["files"]) | set(new_paths)):
        current = content(root, name)
        desired = content(source, name)
        current_bytes[name], desired_bytes[name] = current, desired
        base = manifest["files"].get(name)
        current_digest = hash_bytes(current) if current is not None else None
        desired_digest = hash_bytes(desired) if desired is not None else None
        if base is None:
            action = "add" if current is None and desired is not None else "conflict"
        elif current is None:
            action = "conflict"
        elif current_digest == desired_digest:
            action = "unchanged"
        elif current_digest == base:
            action = "remove" if desired is None else "update"
        elif desired_digest == base:
            action = "preserve"
        else:
            action = "conflict"
        actions.append(
            {"path": name, "action": action, "current": current_digest, "new": desired_digest}
        )
    plan = {
        "schema": "bootcrate-upgrade-plan/v1",
        "base_revision": manifest["source_revision"],
        "actions": actions,
    }
    plan["digest"] = hash_bytes(
        json.dumps(plan, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return plan, current_bytes, desired_bytes


def preview(root: Path, source: Path, manifest: dict, new_paths: list[str] = ()) -> dict:
    root, source = validated_root(root), validated_root(source)
    bootstrap(root)
    return _build_plan(root, source, manifest, list(new_paths))[0]


def _same_content(root: Path, name: str, expected: str | None) -> bool:
    try:
        data = content(root, name)
    except (OSError, ValueError):
        return False
    actual = hash_bytes(data) if data is not None else None
    return actual == expected


def _same_manifest(root: Path, expected: bytes) -> bool:
    try:
        path = _control_path(root, MANIFEST)
        return path.is_file() and path.read_bytes() == expected
    except (OSError, ValueError):
        return False


def _prepare_parent(root: Path, target: Path) -> list[Path]:
    created = []
    missing = []
    current = target.parent
    while current != root and not _lexists(current):
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        _mutator().mkdir(_relative(directory))
        created.append(directory)
        resolve(root, directory.relative_to(root).as_posix())
    if not target.parent.is_dir():
        raise ValueError("Managed target parent is not a directory")
    resolve(root, target.relative_to(root).as_posix())
    return created


def _journal(path: Path, status: str, details: dict) -> None:
    data = _manifest_bytes({"schema": "bootcrate-upgrade-recovery/v1", "status": status, **details})
    staged = path / ("journal-" + secrets.token_hex(8))
    _write_file(staged, data)
    _replace_file(staged, path / "recovery.json")


def apply(
    root: Path,
    source: Path,
    expected_digest: str,
    new_revision: str,
    new_paths: list[str] = (),
) -> dict:
    root, source = validated_root(root), validated_root(source)
    if not isinstance(new_revision, str) or not new_revision:
        raise ValueError("New source revision is required")
    with _locked(root) as control:
        manifest, manifest_before = _read_manifest(root)
        plan, before, approved = _build_plan(root, source, manifest, list(new_paths))
        if plan["digest"] != expected_digest:
            raise ValueError("Plan or file contents changed since review")
        if any(item["action"] == "conflict" for item in plan["actions"]):
            raise ValueError("Resolve all conflicts explicitly before applying")
        changes = [item for item in plan["actions"] if item["action"] in {"add", "remove", "update"}]
        transaction = control / ("bootcrate-upgrade-txn-" + secrets.token_hex(12))
        _mutator().mkdir(_relative(transaction))
        written: dict[str, str | None] = {}
        created_dirs: list[Path] = []
        manifest_after: bytes | None = None
        manifest_written = False
        try:
            for index, item in enumerate(changes):
                name = item["path"]
                if before[name] is not None:
                    _write_file(transaction / ("before-" + str(index)), before[name])
                if item["action"] != "remove":
                    frozen = approved[name]
                    if frozen is None or hash_bytes(frozen) != item["new"]:
                        raise RuntimeError("Approved source buffer is inconsistent")
                    _write_file(transaction / ("approved-" + str(index)), frozen)
            _journal(transaction, "prepared", {"paths": [item["path"] for item in changes]})

            for index, item in enumerate(changes):
                name = item["path"]
                if not _same_manifest(root, manifest_before):
                    raise ValueError("Manifest changed during update")
                if not _same_content(root, name, item["current"]):
                    raise ValueError("Managed destination changed before write: " + name)
                target = resolve(root, name)
                if item["action"] == "remove":
                    _unlink_file(target)
                    written[name] = None
                else:
                    created_dirs.extend(_prepare_parent(root, target))
                    staged = transaction / ("approved-" + str(index))
                    _replace_file(staged, target)
                    written[name] = item["new"]
                if not _same_content(root, name, written[name]):
                    raise ValueError("Managed destination changed at write boundary: " + name)

            if not _same_manifest(root, manifest_before):
                raise ValueError("Manifest changed before commit")
            for name, digest in written.items():
                if not _same_content(root, name, digest):
                    raise ValueError("Managed destination changed before manifest commit: " + name)

            next_manifest = json.loads(json.dumps(manifest))
            for item in plan["actions"]:
                if item["action"] == "remove":
                    next_manifest["files"].pop(item["path"], None)
                elif item["action"] in {"update", "add", "unchanged"}:
                    next_manifest["files"][item["path"]] = item["new"]
            next_manifest["source_revision"] = new_revision
            manifest_after = _manifest_bytes(next_manifest)
            staged_manifest = transaction / "manifest-after"
            _write_file(staged_manifest, manifest_after)
            if not _same_manifest(root, manifest_before):
                raise ValueError("Manifest changed at commit boundary")
            _replace_file(staged_manifest, _control_path(root, MANIFEST))
            manifest_written = True
            if not _same_manifest(root, manifest_after):
                raise RuntimeError("Committed manifest could not be verified")
            for name, digest in written.items():
                if not _same_content(root, name, digest):
                    raise ValueError("Managed destination changed during manifest commit: " + name)
            _journal(transaction, "committed", {"paths": list(written), "revision": new_revision})
        except BaseException as error:
            incomplete = []
            if manifest_written:
                if manifest_after is not None and _same_manifest(root, manifest_after):
                    try:
                        staged = transaction / "manifest-restore"
                        _write_file(staged, manifest_before)
                        _replace_file(staged, _control_path(root, MANIFEST))
                    except (OSError, ValueError, RuntimeError):
                        incomplete.append(MANIFEST.as_posix())
                else:
                    incomplete.append(MANIFEST.as_posix())
            for index in range(len(changes) - 1, -1, -1):
                item = changes[index]
                name = item["path"]
                if name not in written:
                    continue
                if not _same_content(root, name, written[name]):
                    incomplete.append(name)
                    continue
                try:
                    target = resolve(root, name)
                    old = before[name]
                    if old is None:
                        _unlink_file(target, missing_ok=True)
                    else:
                        staged = transaction / ("restore-" + str(index))
                        _write_file(staged, old)
                        _replace_file(staged, target)
                except (OSError, ValueError, RuntimeError):
                    incomplete.append(name)
            for directory in reversed(created_dirs):
                try:
                    _mutator().rmdir(_relative(directory))
                except (OSError, ValueError, RuntimeError):
                    pass
            if incomplete:
                try:
                    _journal(
                        transaction,
                        "recovery_incomplete",
                        {"preserved": sorted(set(incomplete)), "error_type": type(error).__name__},
                    )
                except (OSError, ValueError, RuntimeError):
                    pass
                raise RuntimeError(
                    "Recovery incomplete; concurrent data and transaction evidence were preserved in "
                    + transaction.name
                ) from error
            _cleanup_transaction(transaction)
            raise
        _cleanup_transaction(transaction)
    return {"status": "applied", "paths": [item["path"] for item in changes], "revision": new_revision}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("root", type=Path)
    initialize.add_argument("--revision", required=True)
    initialize.add_argument("paths", nargs="+")
    for command in ("preview", "apply"):
        sub = commands.add_parser(command)
        sub.add_argument("root", type=Path)
        sub.add_argument("source", type=Path)
        sub.add_argument("--new-path", action="append", default=[])
        if command == "apply":
            sub.add_argument("--approved-plan-digest", required=True)
            sub.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = create(args.root, args.revision, args.paths)
        elif args.command == "preview":
            result = preview(args.root, args.source, read(args.root), args.new_path)
        else:
            result = apply(
                args.root, args.source, args.approved_plan_digest, args.revision, args.new_path
            )
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError, RuntimeError) as error:
        print("BLOCKED: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
