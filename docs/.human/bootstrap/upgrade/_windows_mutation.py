"""Handle-relative Windows mutations for the local managed-upgrade transaction.

The project root and every parent directory stay open without FILE_SHARE_DELETE.
Leaf operations use NT RootDirectory handles, never a reconstructed pathname.
This also fails closed if a pinned directory becomes a reparse point in place.
"""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
import errno
import hashlib
import os
from pathlib import Path


_FILE_READ_DATA = 0x0001
_FILE_WRITE_DATA = 0x0002
_FILE_LIST_DIRECTORY = 0x0001
_FILE_READ_ATTRIBUTES = 0x0080
_DELETE = 0x00010000
_SYNCHRONIZE = 0x00100000
_SHARE_READ_WRITE = 0x0003
_SHARE_READ = 0x0001
_OPEN_EXISTING = 3
_FILE_OPEN = 1
_FILE_CREATE = 2
_FILE_DIRECTORY_FILE = 0x0001
_FILE_NON_DIRECTORY_FILE = 0x0040
_FILE_SYNCHRONOUS_IO_NONALERT = 0x0020
_FILE_OPEN_REPARSE_POINT = 0x200000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_ATTRIBUTE_DIRECTORY = 0x0010
_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
_OBJ_CASE_INSENSITIVE = 0x0040
_FILE_ATTRIBUTE_TAG_INFO_CLASS = 9
_FILE_DISPOSITION_INFO_CLASS = 4
_FILE_RENAME_INFORMATION_CLASS = 10
_FILE_LINK_INFORMATION_CLASS = 11
_STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034
_STATUS_OBJECT_NAME_COLLISION = 0xC0000035
_MAX_READ_BYTES = 4 * 1024 * 1024


class _UnicodeString(ctypes.Structure):
    _fields_ = [("Length", ctypes.c_ushort), ("MaximumLength", ctypes.c_ushort),
                ("Buffer", ctypes.c_void_p)]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [("Length", ctypes.c_uint32), ("RootDirectory", ctypes.c_void_p),
                ("ObjectName", ctypes.POINTER(_UnicodeString)),
                ("Attributes", ctypes.c_uint32), ("SecurityDescriptor", ctypes.c_void_p),
                ("SecurityQualityOfService", ctypes.c_void_p)]


class _IoStatusBlock(ctypes.Structure):
    _fields_ = [("Status", ctypes.c_void_p), ("Information", ctypes.c_size_t)]


class _FileAttributeTagInfo(ctypes.Structure):
    _fields_ = [("FileAttributes", ctypes.c_uint32), ("ReparseTag", ctypes.c_uint32)]


class _RelativeNameHeader(ctypes.Structure):
    _fields_ = [("ReplaceIfExists", ctypes.c_uint32),
                ("RootDirectory", ctypes.c_void_p),
                ("FileNameLength", ctypes.c_uint32)]


if os.name == "nt":
    _kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    _native = ctypes.WinDLL("ntdll")
    _kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                    ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                                    ctypes.c_void_p]
    _kernel.CreateFileW.restype = ctypes.c_void_p
    _kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    _kernel.CloseHandle.restype = ctypes.c_int
    _kernel.GetFileInformationByHandleEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                                      ctypes.c_void_p, ctypes.c_uint32]
    _kernel.GetFileInformationByHandleEx.restype = ctypes.c_int
    _kernel.GetFinalPathNameByHandleW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p,
                                                  ctypes.c_uint32, ctypes.c_uint32]
    _kernel.GetFinalPathNameByHandleW.restype = ctypes.c_uint32
    _kernel.SetFileInformationByHandle.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                                   ctypes.c_void_p, ctypes.c_uint32]
    _kernel.SetFileInformationByHandle.restype = ctypes.c_int
    _kernel.ReadFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
                                 ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
    _kernel.ReadFile.restype = ctypes.c_int
    _native.NtCreateFile.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_uint32,
                                     ctypes.POINTER(_ObjectAttributes),
                                     ctypes.POINTER(_IoStatusBlock), ctypes.c_void_p,
                                     ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                                     ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]
    _native.NtCreateFile.restype = ctypes.c_long
    _native.NtSetInformationFile.argtypes = [ctypes.c_void_p, ctypes.POINTER(_IoStatusBlock),
                                             ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int]
    _native.NtSetInformationFile.restype = ctypes.c_long


def _parts(relative: Path | str) -> tuple[str, ...]:
    value = Path(relative)
    if value.is_absolute() or value.drive or not value.parts:
        raise ValueError("Windows mutation requires a root-relative path")
    parts = value.parts
    if any(part in {"", ".", ".."} or part.endswith((" ", "."))
           or any(character in part for character in (":", "\\", "/", "\x00"))
           for part in parts):
        raise ValueError("Unsafe Windows mutation path")
    return parts


def _close(handle: int | None) -> None:
    if handle is not None and os.name == "nt":
        _kernel.CloseHandle(handle)


def _nt_error(operation: str, status: int) -> OSError:
    return OSError(operation + " failed with NTSTATUS 0x" + format(status & 0xffffffff, "08x"))


def _attributes(handle: int) -> int:
    info = _FileAttributeTagInfo()
    if not _kernel.GetFileInformationByHandleEx(
            handle, _FILE_ATTRIBUTE_TAG_INFO_CLASS, ctypes.byref(info), ctypes.sizeof(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    return info.FileAttributes


def _require_kind(handle: int, *, directory: bool) -> None:
    attributes = _attributes(handle)
    if attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError("Windows mutation path is a reparse point")
    if bool(attributes & _FILE_ATTRIBUTE_DIRECTORY) != directory:
        raise ValueError("Windows mutation path has the wrong file type")


def _nt_open(parent: int, basename: str, access: int, disposition: int,
             *, directory: bool, share: int = _SHARE_READ_WRITE) -> int:
    raw = ctypes.create_unicode_buffer(basename)
    encoded = basename.encode("utf-16-le")
    name = _UnicodeString(len(encoded), len(encoded) + 2, ctypes.cast(raw, ctypes.c_void_p))
    attributes = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), parent,
                                   ctypes.pointer(name), _OBJ_CASE_INSENSITIVE, None, None)
    result = ctypes.c_void_p()
    status_block = _IoStatusBlock()
    options = (_FILE_SYNCHRONOUS_IO_NONALERT | _FILE_OPEN_REPARSE_POINT |
               (_FILE_DIRECTORY_FILE if directory else _FILE_NON_DIRECTORY_FILE))
    status = _native.NtCreateFile(ctypes.byref(result), access | _FILE_READ_ATTRIBUTES,
                                  ctypes.byref(attributes),
                                  ctypes.byref(status_block), None, 0,
                                  share, disposition, options, None, 0)
    if status != 0:
        if disposition == _FILE_CREATE and status & 0xffffffff == _STATUS_OBJECT_NAME_COLLISION:
            raise FileExistsError(errno.EEXIST, "Windows mutation target already exists", basename)
        raise _nt_error("NtCreateFile", status)
    handle = result.value
    try:
        _require_kind(handle, directory=directory)
    except BaseException:
        _close(handle)
        raise
    return handle


def _final_path(handle: int) -> str:
    length = _kernel.GetFinalPathNameByHandleW(handle, None, 0, 0)
    if not length:
        raise ctypes.WinError(ctypes.get_last_error())
    buffer = ctypes.create_unicode_buffer(length + 1)
    result = _kernel.GetFinalPathNameByHandleW(handle, buffer, length + 1, 0)
    if not result or result >= length + 1:
        raise ctypes.WinError(ctypes.get_last_error())
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def _relative_info(parent: int, basename: str, *, replace: bool) -> ctypes.Array:
    encoded = basename.encode("utf-16-le")
    name_offset = _RelativeNameHeader.FileNameLength.offset + ctypes.sizeof(ctypes.c_uint32)
    buffer = ctypes.create_string_buffer(max(ctypes.sizeof(_RelativeNameHeader),
                                              name_offset + len(encoded) + 2))
    ctypes.c_uint32.from_buffer(buffer, _RelativeNameHeader.ReplaceIfExists.offset).value = int(replace)
    ctypes.c_void_p.from_buffer(buffer, _RelativeNameHeader.RootDirectory.offset).value = parent
    ctypes.c_uint32.from_buffer(buffer, _RelativeNameHeader.FileNameLength.offset).value = len(encoded)
    ctypes.memmove(ctypes.addressof(buffer) + name_offset, encoded, len(encoded))
    return buffer


def _verify_source(handle: int, expected_digest: str | None) -> None:
    if expected_digest is None:
        return
    if (not isinstance(expected_digest, str) or len(expected_digest) != 64 or
            any(character not in "0123456789abcdef" for character in expected_digest)):
        raise ValueError("Invalid staged source digest")
    digest = hashlib.sha256()
    total = 0
    buffer = ctypes.create_string_buffer(65536)
    while True:
        count = ctypes.c_uint32()
        if not _kernel.ReadFile(handle, buffer, len(buffer), ctypes.byref(count), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if not count.value:
            break
        total += count.value
        if total > _MAX_READ_BYTES:
            raise ValueError("Staged source exceeds its read limit")
        digest.update(buffer.raw[:count.value])
    if digest.hexdigest() != expected_digest:
        raise ValueError("Frozen staged bytes changed before mutation")


class WindowsMutator:
    """Mutate project-root-relative paths using pinned directory handles."""

    def __init__(self, root: Path):
        if os.name != "nt":
            raise OSError("WindowsMutator is only available on Windows")
        root = Path(root).absolute()
        handle = _kernel.CreateFileW(str(root), _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES,
                                     _SHARE_READ_WRITE, None, _OPEN_EXISTING,
                                     _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
                                     None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            _require_kind(handle, directory=True)
            if os.path.normcase(os.path.normpath(_final_path(handle))) != os.path.normcase(os.path.normpath(str(root))):
                raise ValueError("Windows mutation root does not match its opened directory")
        except BaseException:
            _close(handle)
            raise
        self.root = root
        self._root = handle
        self.created: set[Path] = set()

    def __enter__(self) -> WindowsMutator:
        return self

    def __exit__(self, _type, _value, _traceback) -> None:
        self.close()

    def close(self) -> None:
        if self._root is not None:
            _close(self._root)
            self._root = None

    @contextmanager
    def _parent(self, relative: Path | str):
        if self._root is None:
            raise ValueError("WindowsMutator is closed")
        parts = _parts(relative)
        opened = []
        parent = self._root
        try:
            for component in parts[:-1]:
                parent = _nt_open(parent, component,
                                  _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                                  _FILE_OPEN, directory=True)
                opened.append(parent)
            _require_kind(parent, directory=True)
            yield parent, parts[-1]
        finally:
            for handle in reversed(opened):
                _close(handle)

    def write_new(self, relative: Path | str, data: bytes) -> None:
        if not isinstance(data, bytes):
            raise TypeError("Windows mutation data must be bytes")
        with self._parent(relative) as (parent, basename):
            handle = _nt_open(parent, basename, _FILE_WRITE_DATA | _SYNCHRONIZE,
                              _FILE_CREATE, directory=False)
            try:
                import msvcrt
                descriptor = msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
                handle = None
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            finally:
                _close(handle)

    def read(self, relative: Path | str, *, max_bytes: int = _MAX_READ_BYTES) -> bytes:
        if max_bytes < 0:
            raise ValueError("Negative Windows mutation read limit")
        with self._parent(relative) as (parent, basename):
            handle = _nt_open(parent, basename,
                              _FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                              _FILE_OPEN, directory=False)
            try:
                import msvcrt
                descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
                handle = None
                with os.fdopen(descriptor, "rb") as stream:
                    data = stream.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise ValueError("Windows mutation file exceeds its read limit")
                return data
            finally:
                _close(handle)

    def replace(self, source: Path | str, destination: Path | str,
                *, expected_digest: str | None = None) -> None:
        with self._parent(source) as (source_parent, source_name):
            handle = _nt_open(source_parent, source_name,
                              _DELETE | _FILE_READ_DATA | _SYNCHRONIZE,
                              _FILE_OPEN, directory=False, share=_SHARE_READ)
            try:
                _verify_source(handle, expected_digest)
                with self._parent(destination) as (destination_parent, destination_name):
                    info = _relative_info(destination_parent, destination_name, replace=True)
                    status_block = _IoStatusBlock()
                    status = _native.NtSetInformationFile(handle, ctypes.byref(status_block),
                                                           info, len(info),
                                                           _FILE_RENAME_INFORMATION_CLASS)
                    if status != 0:
                        raise _nt_error("NtSetInformationFile rename", status)
            finally:
                _close(handle)

    def unlink(self, relative: Path | str, *, missing_ok: bool = False) -> None:
        with self._parent(relative) as (parent, basename):
            try:
                handle = _nt_open(parent, basename, _DELETE | _SYNCHRONIZE,
                                  _FILE_OPEN, directory=False)
            except OSError as error:
                if missing_ok and ("0x" + format(_STATUS_OBJECT_NAME_NOT_FOUND, "08x")) in str(error):
                    return
                raise
            try:
                remove = ctypes.c_byte(1)
                if not _kernel.SetFileInformationByHandle(handle, _FILE_DISPOSITION_INFO_CLASS,
                                                           ctypes.byref(remove), ctypes.sizeof(remove)):
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                _close(handle)

    def mkdir(self, relative: Path | str) -> None:
        with self._parent(relative) as (parent, basename):
            handle = _nt_open(parent, basename,
                              _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                              _FILE_CREATE, directory=True)
            _close(handle)

    def rmdir(self, relative: Path | str) -> None:
        with self._parent(relative) as (parent, basename):
            handle = _nt_open(parent, basename, _DELETE | _FILE_LIST_DIRECTORY | _SYNCHRONIZE,
                              _FILE_OPEN, directory=True)
            try:
                remove = ctypes.c_byte(1)
                if not _kernel.SetFileInformationByHandle(handle, _FILE_DISPOSITION_INFO_CLASS,
                                                           ctypes.byref(remove), ctypes.sizeof(remove)):
                    raise ctypes.WinError(ctypes.get_last_error())
            finally:
                _close(handle)

    def link(self, source: Path | str, destination: Path | str,
             *, expected_digest: str | None = None) -> None:
        """Create a no-overwrite hard link; unsupported native behavior fails closed."""
        with self._parent(source) as (source_parent, source_name):
            handle = _nt_open(source_parent, source_name,
                              _FILE_READ_DATA | _SYNCHRONIZE,
                              _FILE_OPEN, directory=False, share=_SHARE_READ)
            try:
                _verify_source(handle, expected_digest)
                with self._parent(destination) as (destination_parent, destination_name):
                    info = _relative_info(destination_parent, destination_name, replace=False)
                    status_block = _IoStatusBlock()
                    status = _native.NtSetInformationFile(handle, ctypes.byref(status_block),
                                                           info, len(info), _FILE_LINK_INFORMATION_CLASS)
                    if status != 0:
                        raise _nt_error("NtSetInformationFile link", status)
            finally:
                _close(handle)
