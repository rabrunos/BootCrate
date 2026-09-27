"""Version-contract regressions for legacy v2 and declarative v3 profiles."""
from pathlib import Path
import json
import tempfile
import unittest

import validate as v
from validation_core import validate_version_contract


class VersionCompatibilityTests(unittest.TestCase):
    def write(self, root: Path, name: str, content: str) -> None:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def support_files(self, root: Path) -> None:
        self.write(root, "PROJECT_GUIDE.md", "# Project guide\n")
        self.write(root, "AGENTS.md", "# Codex rules\n")
        self.write(root, ".codex/config.toml", 'model_reasoning_effort = "high"\n')
        self.write(root, "docs/.ai/SECURITY_BASELINE.md", "# Controls\n")

    def v2_profile(self, source: str) -> dict:
        return {
            "schema": "project-profile/v2",
            "project": {"name": "Legacy example", "kind": "cli", "summary": "Synthetic fixture"},
            "owner": {"repository_language": "en", "report_language": "pt-BR"},
            "workflow": {"tracking": "github_issues", "primary_orchestrator": "chatgpt",
                         "fallback_planners": [], "implementation_harnesses": ["codex"]},
            "versioning": {"required": True, "canonical_source": source, "format": "native",
                           "target_version_in_prompt_h1": True, "target_version_in_commit": True,
                           "target_version_in_report_h1": True, "continuations_reuse_target": True},
            "security": {"exposure": "local", "data_classes": [], "untrusted_inputs": [],
                         "modules": [], "control_map": "docs/.ai/SECURITY_BASELINE.md",
                         "verification_commands": []},
        }

    def v3_profile(self, source: str, reader: str, value_path: str) -> dict:
        profile = v.load_json(v.ROOT / "docs/.ai/project-profile.json")
        profile["project"] = {"name": "Declarative example", "kind": "cli",
                              "summary": "Synthetic fixture"}
        profile["workflow"]["implementation_harnesses"] = ["codex"]
        profile["security"].update(exposure="local", control_map="docs/.ai/SECURITY_BASELINE.md")
        profile["versioning"].update(canonical_source=source, reader=reader,
                                     value_path=value_path, format="native",
                                     history_source="HISTORY.md",
                                     history_format="markdown-headings", mirrors=[])
        return profile

    def schema_and_finalization(self, root: Path, profile: dict) -> None:
        v.schema_check(v.profile_schema(v.ROOT / "docs/.ai/schemas", profile), profile)
        v.materialized_profile(profile, root)

    def test_v2_sources_finalize_without_invented_reader_path_or_history(self):
        for source, body in (
            ("VERSION", "1.0\n"),
            ("package.json", json.dumps({"name": "legacy", "version": "2.1"})),
            ("pyproject.toml", '[project]\nversion = "3.2"\n'),
        ):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.support_files(root)
                self.write(root, source, body)
                profile = self.v2_profile(source)
                self.schema_and_finalization(root, profile)
                self.assertIsNone(validate_version_contract(profile, root))
                self.assertEqual(profile["schema"], "project-profile/v2")
                self.assertNotIn("value_path", profile["versioning"])
                self.assertNotIn("history_source", profile["versioning"])
                self.assertFalse((root / "CHANGELOG.md").exists())

    def test_v2_canonical_source_still_must_be_a_safe_local_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.support_files(root)
            for source, message in (("missing.json", "Missing canonical version"),
                                    ("../outside.json", "Unsafe canonical version")):
                with self.subTest(source=source):
                    profile = self.v2_profile(source)
                    v.schema_check(v.profile_schema(v.ROOT / "docs/.ai/schemas", profile), profile)
                    with self.assertRaisesRegex(ValueError, message):
                        v.materialized_profile(profile, root)

    def test_sensitive_version_metadata_names_are_rejected_in_v2_and_v3(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.support_files(root)
            self.write(root, "VERSION", "1.0\n")
            self.write(root, "HISTORY.md", "# History\n\n## v1.0 - Release\n")
            for name in (".env.production", "credentials.json", "secrets.toml", "private.key"):
                with self.subTest(name=name):
                    self.write(root, name, "1.0\n")
                    legacy = self.v2_profile(name)
                    with self.assertRaisesRegex(ValueError, "Sensitive canonical version reference"):
                        self.schema_and_finalization(root, legacy)
                    for field in ("canonical_source", "mirror", "history_source"):
                        with self.subTest(field=field):
                            profile = self.v3_profile("VERSION", "plain", "")
                            profile["versioning"].pop("value_path", None)
                            if field == "mirror":
                                profile["versioning"]["mirrors"] = [{"path": name, "reader": "plain"}]
                            else:
                                profile["versioning"][field] = name
                            with self.assertRaisesRegex(ValueError, "Sensitive .* reference"):
                                self.schema_and_finalization(root, profile)
            nested = "nested/secrets.data/VERSION"
            self.write(root, nested, "1.0\n")
            with self.assertRaisesRegex(ValueError, "Sensitive canonical version reference"):
                self.schema_and_finalization(root, self.v2_profile(nested))

    def test_v3_json_path_history_and_mirror_remain_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.support_files(root)
            self.write(root, "package.json", json.dumps({"meta": {"version": "2.3"}}))
            self.write(root, "mirror.json", json.dumps({"version": "2.3"}))
            self.write(root, "HISTORY.md", "# History\n\n## v2.3 - Release\n")
            profile = self.v3_profile("package.json", "json", "/meta/version")
            profile["versioning"]["mirrors"] = [{"path": "mirror.json", "reader": "json",
                                                  "value_path": "/version"}]
            self.schema_and_finalization(root, profile)
            self.assertEqual(validate_version_contract(profile, root), "2.3")
            del profile["versioning"]["value_path"]
            with self.assertRaisesRegex(ValueError, "value path"):
                v.materialized_profile(profile, root)
            profile["versioning"]["value_path"] = "/meta/version"
            self.write(root, "mirror.json", json.dumps({"version": "2.4"}))
            with self.assertRaisesRegex(ValueError, "mirror diverge"):
                v.materialized_profile(profile, root)
            self.write(root, "mirror.json", json.dumps({"version": "2.3"}))
            self.write(root, "HISTORY.md", "# History\n\n## v2.4 - Other\n")
            with self.assertRaisesRegex(ValueError, "no entry"):
                v.materialized_profile(profile, root)

    def test_v3_toml_value_path_and_required_metadata_remain_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.support_files(root)
            self.write(root, "pyproject.toml", '[project]\nversion = "3.2"\n')
            self.write(root, "HISTORY.md", "# History\n\n## v3.2 - Release\n")
            profile = self.v3_profile("pyproject.toml", "toml", "/project/version")
            self.schema_and_finalization(root, profile)
            self.assertEqual(validate_version_contract(profile, root), "3.2")
            del profile["versioning"]["value_path"]
            with self.assertRaisesRegex(ValueError, "value path"):
                v.materialized_profile(profile, root)
            profile["versioning"]["value_path"] = "/project/version"
            for key in ("reader", "history_source", "history_format", "mirrors"):
                with self.subTest(key=key):
                    missing = json.loads(json.dumps(profile))
                    del missing["versioning"][key]
                    with self.assertRaisesRegex(ValueError, "Schema failure"):
                        v.schema_check(v.profile_schema(v.ROOT / "docs/.ai/schemas", missing), missing)

    def test_v3_history_requires_exact_version_token(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.support_files(root)
            self.write(root, "VERSION", "1.0\n")
            profile = self.v3_profile("VERSION", "plain", "")
            profile["versioning"].pop("value_path")
            for heading in ("## v1.0-beta — Prerelease", "## v1.0+build — Build"):
                with self.subTest(heading=heading):
                    self.write(root, "HISTORY.md", "# History\n\n" + heading + "\n")
                    with self.assertRaisesRegex(ValueError, "no entry for integrated version 1.0"):
                        self.schema_and_finalization(root, profile)
            for heading in ("## v1.0 — Release", "## [v1.0] - Release"):
                with self.subTest(heading=heading):
                    self.write(root, "HISTORY.md", "# History\n\n" + heading + "\n")
                    self.schema_and_finalization(root, profile)

            for indent in range(1,4):
                with self.subTest(indent=indent):
                    self.write(root, "HISTORY.md", "# History\n\n" +
                               " " * indent + "## v1.0 - Release\n")
                    self.schema_and_finalization(root, profile)
            self.write(root, "HISTORY.md", "# History\n\n    ## v1.0 - Code block\n")
            with self.assertRaisesRegex(ValueError, "no entry for integrated version 1.0"):
                self.schema_and_finalization(root, profile)

    def test_v3_history_ignores_fenced_and_commented_headings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.support_files(root)
            self.write(root, "VERSION", "1.0\n")
            profile = self.v3_profile("VERSION", "plain", "")
            profile["versioning"].pop("value_path")
            hidden = (
                "```markdown\n## v1.0 - Example\n```",
                "  ```markdown\n  ## v1.0 - Example\n  ```",
                "~~~~ markdown\n## v1.0 - Example\n~~~~",
                "<!--\n## v1.0 - Draft\n-->",
                "<!--\n  ## v1.0 - Draft\n-->",
                "<!-- ## v1.0 - Draft -->",
                "<!-- note -->## v1.0 - Draft",
                "```markdown\n<!-- unfinished comment\n```",
                "<script>\n## v1.0 - Draft\n</script>",
                "<PRE class=\"sample\">\n## v1.0 - Draft\n</PRE>",
                "<style>\n## v1.0 - Draft\n</style>",
                "<textarea>\n## v1.0 - Draft\n</textarea>",
                "<div>\n## v1.0 - Draft\n</div>",
            )
            for section in hidden:
                with self.subTest(section=section):
                    self.write(root, "HISTORY.md", "# History\n\n" + section + "\n")
                    with self.assertRaisesRegex(ValueError, "no entry for integrated version 1.0"):
                        self.schema_and_finalization(root, profile)
                    self.write(root, "HISTORY.md", "# History\n\n" + section +
                               "\n\n## v1.0 - Release\n")
                    self.schema_and_finalization(root, profile)
            self.write(root, "HISTORY.md", "<script>\n## v1.0 - Draft\n</script>\n"
                       "## v1.0 - Release\n")
            self.schema_and_finalization(root, profile)

    def test_v3_numeric_versions_must_be_finite(self):
        sources = (
            ("json", "package.json", "{\"version\": NaN}"),
            ("json", "package.json", "{\"version\": Infinity}"),
            ("json", "package.json", "{\"version\": -Infinity}"),
            ("json", "package.json", "{\"version\": 1e999}"),
            ("toml", "pyproject.toml", "version = nan\n"),
            ("toml", "pyproject.toml", "version = inf\n"),
            ("toml", "pyproject.toml", "version = -inf\n"),
        )
        for reader, source, body in sources:
            with self.subTest(reader=reader, body=body), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.support_files(root)
                self.write(root, source, body)
                self.write(root, "HISTORY.md", "# History\n\n## v1.25 - Release\n")
                profile = self.v3_profile(source, reader, "/version")
                with self.assertRaisesRegex(ValueError, "numeric value must be finite"):
                    self.schema_and_finalization(root, profile)

        for reader, source, body in (("json", "package.json", '{"version": 1.25}'),
                                     ("toml", "pyproject.toml", "version = 1.25\n")):
            with self.subTest(reader=reader, finite=True), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.support_files(root)
                self.write(root, source, body)
                self.write(root, "HISTORY.md", "# History\n\n## v1.25 - Release\n")
                profile = self.v3_profile(source, reader, "/version")
                self.schema_and_finalization(root, profile)
                self.assertEqual(validate_version_contract(profile, root), "1.25")


if __name__ == "__main__":
    unittest.main()
