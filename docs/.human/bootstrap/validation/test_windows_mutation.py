"""Native Windows mutation checks; Linux uses the POSIX dir-fd path instead."""
import ctypes
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import struct
import tempfile
import unittest
from unittest.mock import patch


MODULE = Path(__file__).resolve().parents[1] / 'upgrade' / '_windows_mutation.py'
spec = importlib.util.spec_from_file_location('windows_mutation', MODULE)
windows_mutation = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(windows_mutation)


@unittest.skipUnless(os.name == 'nt', 'Windows native mutation only')
class WindowsMutationTests(unittest.TestCase):
    def set_junction_on_open_directory(self, directory, outside):
        """Simulate an in-place reparse change after the directory was pinned."""
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                       ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                                       ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.DeviceIoControl.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
                                           ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
                                           ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p]
        kernel.DeviceIoControl.restype = ctypes.c_int
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle.restype = ctypes.c_int
        handle = kernel.CreateFileW(str(directory), 0x100, 3, None, 3,
                                    0x02000000 | 0x00200000, None)
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            substitute = ('\\??\\' + str(outside)).encode('utf-16-le')
            printable = str(outside).encode('utf-16-le')
            names = substitute + b'\x00\x00' + printable + b'\x00\x00'
            reparse = struct.pack('<IHHHHHH', 0xA0000003, 8 + len(names), 0,
                                  0, len(substitute), len(substitute) + 2,
                                  len(printable)) + names
            buffer = ctypes.create_string_buffer(reparse)
            returned = ctypes.c_uint32()
            if not kernel.DeviceIoControl(handle, 0x000900A4, buffer, len(reparse),
                                          None, 0, ctypes.byref(returned), None):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            kernel.CloseHandle(handle)

    def test_relative_create_replace_remove_and_directory_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with windows_mutation.WindowsMutator(root) as mutation:
                mutation.mkdir('dir')
                mutation.write_new('dir/staged.txt', b'approved bytes')
                self.assertEqual(mutation.read('dir/staged.txt'), b'approved bytes')
                with self.assertRaises(OSError):
                    mutation.write_new('dir/staged.txt', b'unapproved bytes')
                mutation.write_new('dir/target.txt', b'old bytes')
                mutation.replace('dir/staged.txt', 'dir/target.txt')
                self.assertEqual(mutation.read('dir/target.txt'), b'approved bytes')
                mutation.unlink('dir/target.txt')
                mutation.unlink('dir/target.txt', missing_ok=True)
                mutation.rmdir('dir')
            self.assertFalse((root / 'dir').exists())

    def test_manifest_hard_link_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with windows_mutation.WindowsMutator(root) as mutation:
                mutation.mkdir('.local')
                mutation.write_new('.local/bootcrate-managed.lock', b'first lock')
                with self.assertRaises(FileExistsError):
                    mutation.write_new('.local/bootcrate-managed.lock', b'second lock')
                self.assertEqual(mutation.read('.local/bootcrate-managed.lock'), b'first lock')
                mutation.write_new('.local/staged', b'manifest bytes')
                expected = hashlib.sha256(b'manifest bytes').hexdigest()
                mutation.link('.local/staged', '.local/manifest', expected_digest=expected)
                self.assertEqual(mutation.read('.local/manifest'), b'manifest bytes')
                with self.assertRaises(OSError):
                    mutation.link('.local/staged', '.local/manifest')
                self.assertEqual(mutation.read('.local/manifest'), b'manifest bytes')
                (root / '.local/staged').write_bytes(b'concurrent edit')
                with self.assertRaisesRegex(ValueError, 'Frozen staged bytes changed'):
                    mutation.link('.local/staged', '.local/other', expected_digest=expected)
                self.assertFalse((root / '.local/other').exists())
                mutation.unlink('.local/manifest')
                mutation.unlink('.local/staged')
                mutation.unlink('.local/bootcrate-managed.lock')
                mutation.rmdir('.local')

    def test_replace_checks_frozen_bytes_and_blocks_in_flight_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            approved = b'approved bytes'
            expected = hashlib.sha256(approved).hexdigest()
            original_info = windows_mutation._relative_info
            attempted_write = False

            def concurrent_write_attempt(parent, basename, *, replace):
                nonlocal attempted_write
                kernel = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32,
                                               ctypes.c_uint32, ctypes.c_void_p,
                                               ctypes.c_uint32, ctypes.c_uint32,
                                               ctypes.c_void_p]
                kernel.CreateFileW.restype = ctypes.c_void_p
                handle = kernel.CreateFileW(str(root / 'dir/staged'), 0x0002, 7,
                                            None, 3, 0, None)
                attempted_write = True
                self.assertEqual(handle, ctypes.c_void_p(-1).value)
                self.assertEqual(ctypes.get_last_error(), 32)  # Sharing violation.
                return original_info(parent, basename, replace=replace)

            with windows_mutation.WindowsMutator(root) as mutation:
                mutation.mkdir('dir')
                mutation.write_new('dir/staged', approved)
                mutation.write_new('dir/target', b'old bytes')
                with patch.object(windows_mutation, '_relative_info',
                                  side_effect=concurrent_write_attempt):
                    mutation.replace('dir/staged', 'dir/target', expected_digest=expected)
                self.assertTrue(attempted_write)
                self.assertEqual(mutation.read('dir/target'), approved)

                mutation.write_new('dir/tampered', approved)
                (root / 'dir/tampered').write_bytes(b'concurrent edit')
                with self.assertRaisesRegex(ValueError, 'Frozen staged bytes changed'):
                    mutation.replace('dir/tampered', 'dir/target', expected_digest=expected)
                self.assertEqual(mutation.read('dir/target'), approved)

    def test_parent_junction_and_unsafe_relative_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'project'
            outside = Path(directory) / 'outside'
            root.mkdir(); outside.mkdir()
            (outside / 'sentinel.txt').write_bytes(b'external bytes')
            with windows_mutation.WindowsMutator(root) as mutation:
                for path in ('../outside/sentinel.txt', 'C:/outside/file.txt',
                             'dir/file.txt:stream'):
                    with self.subTest(path=path), self.assertRaises(ValueError):
                        mutation.write_new(path, b'approved bytes')
                link = root / 'dir'
                subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(outside)],
                               check=True, capture_output=True)
                try:
                    with self.assertRaises((ValueError, OSError)):
                        mutation.replace('dir/sentinel.txt', 'dir/target.txt')
                    with self.assertRaises((ValueError, OSError)):
                        mutation.write_new('dir/target.txt', b'approved bytes')
                finally:
                    os.rmdir(link)
            self.assertEqual((outside / 'sentinel.txt').read_bytes(), b'external bytes')
            self.assertFalse((outside / 'target.txt').exists())

    def test_in_place_junction_conversion_cannot_redirect_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'project'
            outside = Path(directory) / 'outside'
            root.mkdir(); outside.mkdir()
            (root / 'dir').mkdir()
            (outside / 'target.txt').write_bytes(b'external sentinel')
            converted = False
            original_info = windows_mutation._relative_info

            def convert_before_native_rename(parent, basename, *, replace):
                nonlocal converted
                self.set_junction_on_open_directory(root / 'dir', outside)
                converted = True
                return original_info(parent, basename, replace=replace)

            try:
                with windows_mutation.WindowsMutator(root) as mutation:
                    mutation.write_new('staged.txt', b'approved bytes')
                    with patch.object(windows_mutation, '_relative_info',
                                      side_effect=convert_before_native_rename):
                        with self.assertRaises(OSError):
                            mutation.replace('staged.txt', 'dir/target.txt')
                    self.assertTrue(converted)
                    self.assertEqual(mutation.read('staged.txt'), b'approved bytes')
                self.assertEqual((outside / 'target.txt').read_bytes(), b'external sentinel')
            finally:
                if (root / 'dir').is_junction():
                    os.rmdir(root / 'dir')


if __name__ == '__main__':
    unittest.main()
