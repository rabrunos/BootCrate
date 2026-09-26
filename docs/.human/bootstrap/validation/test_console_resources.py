"""Focused local-resource regressions for the selected Project Console."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import validate as v


spec = importlib.util.spec_from_file_location(
    "verify_materialized_console_resources", v.BOOT / "validation/verify-materialized.py"
)
verify_materialized = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_materialized)


class ConsoleResourceTests(unittest.TestCase):
    INDEX = ('<!doctype html><link rel="stylesheet" href="styles.css">'
             '<script src="preset.js"></script>'
             '<script src="execution-profile.js"></script>'
             '<script src="console.js"></script>')

    def fixture(self, root):
        profile = v.load_json(v.ROOT / "docs/.ai/project-profile.json")
        profile["project"] = {"name": "Example", "kind": "static", "summary": "Synthetic fixture"}
        profile["versioning"].update(
            canonical_source="VERSION", reader="plain", format="project convention",
            history_source="CHANGELOG.md", history_format="markdown-headings", mirrors=[]
        )
        profile["security"].update(exposure="local", control_map="docs/.ai/SECURITY_BASELINE.md")
        profile["workflow"]["implementation_harnesses"] = ["codex"]
        profile["console"]["enabled"] = True
        for name, body in {
            "docs/.ai/SECURITY_BASELINE.md": "# Controls\n",
            "docs/.ai/project-profile.json": json.dumps(profile),
            "PROJECT_GUIDE.md": "# Project Guide\n",
            "README.md": "# Example\n",
            "VERSION": "1.0\n",
            "CHANGELOG.md": "# Changelog\n\n## v1.0 — Initial\n",
            "AGENTS.md": "# Codex rules\n",
            ".codex/config.toml": ('model_reasoning_effort = "high"\n'
                                   'sandbox_mode = "workspace-write"\n'
                                   'approval_policy = "on-request"\n'
                                   'approvals_reviewer = "user"\n'),
            "project-console/index.html": self.INDEX,
            "project-console/styles.css": "body { color: black; }\n",
            "project-console/preset.js": "/* fixture */\n",
            "project-console/execution-profile.js": "/* fixture */\n",
            "project-console/console.js": "/* fixture */\n",
        }.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return root / "project-console"

    def profile_check(self, root):
        return next(entry for entry in verify_materialized.inspect(root)
                    if entry["check_id"] == "profile.finalized")

    def test_local_resources_and_navigation_links_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            console = self.fixture(root)
            (console / "assets").mkdir()
            (console / "assets/extra.js").write_text("/* local */\n", encoding="utf-8")
            (console / "index.html").write_text(
                self.INDEX + '<script src="assets/extra.js"></script>'
                '<a href="https://example.invalid/project">Navigation only</a>', encoding="utf-8"
            )
            self.assertEqual(self.profile_check(root)["status"], "pass")

    def test_remote_script_and_stylesheet_are_rejected(self):
        cases = [
            '<script src="https://example.invalid/x.js"></script>',
            '<script src="//example.invalid/x.js"></script>',
            '<link rel="stylesheet" href="https://example.invalid/x.css">',
            '<script src="data:text/javascript,alert(1)"></script>',
            '<script src="javascript:alert(1)"></script>',
            '<script src="file:///tmp/x.js"></script>',
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            console = self.fixture(root)
            for extra in cases:
                with self.subTest(extra=extra):
                    (console / "index.html").write_text(self.INDEX + extra, encoding="utf-8")
                    result = self.profile_check(root)
                    self.assertEqual(result["status"], "fail")
                    self.assertIn("non-local reference", result["summary"])

    def test_absolute_traversal_and_base_urls_are_rejected(self):
        cases = [
            ('<script src="/tmp/x.js"></script>', "must be relative"),
            ('<script src="../outside.js"></script>', "escapes project-console"),
            ('<script src="%2e%2e/outside.js"></script>', "escapes project-console"),
            ('<base href="https://example.invalid/">', "base URL"),
        ]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            console = self.fixture(root)
            (root / "outside.js").write_text("/* outside */\n", encoding="utf-8")
            for extra, message in cases:
                with self.subTest(extra=extra):
                    (console / "index.html").write_text(self.INDEX + extra, encoding="utf-8")
                    result = self.profile_check(root)
                    self.assertEqual(result["status"], "fail")
                    self.assertIn(message, result["summary"])

    def test_link_outside_console_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            console = self.fixture(root)
            outside = root / "outside"
            outside.mkdir()
            (outside / "escape.js").write_text("/* outside */\n", encoding="utf-8")
            link = console / "escape"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                if os.name != "nt":
                    raise
                subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
                               check=True, capture_output=True)
            try:
                (console / "index.html").write_text(
                    self.INDEX + '<script src="escape/escape.js"></script>', encoding="utf-8"
                )
                result = self.profile_check(root)
                self.assertEqual(result["status"], "fail")
                self.assertIn("escapes project-console", result["summary"])
            finally:
                if link.is_symlink():
                    link.unlink()
                else:
                    os.rmdir(link)  # Windows junction fallback.

    def test_css_imports_and_urls_must_remain_local(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            console = self.fixture(root)
            (console / "assets").mkdir()
            (console / "assets/more.css").write_text("p { color: blue; }\n", encoding="utf-8")
            (console / "assets/font.woff").write_bytes(b"synthetic font")
            (console / "styles.css").write_text(
                '@import "assets/more.css"; p { background: url("assets/font.woff"); }\n',
                encoding="utf-8"
            )
            self.assertEqual(self.profile_check(root)["status"], "pass")
            for css in ('@import "https://example.invalid/x.css";',
                        'p { background: url(https://example.invalid/x.png); }',
                        '@import url(//example.invalid/x.css);'):
                with self.subTest(css=css):
                    (console / "styles.css").write_text(css, encoding="utf-8")
                    result = self.profile_check(root)
                    self.assertEqual(result["status"], "fail")
                    self.assertIn("non-local reference", result["summary"])


if __name__ == "__main__":
    unittest.main()
