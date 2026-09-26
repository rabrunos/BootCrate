from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ADAPTERS = HERE.parent / "library" / "adapters"
spec = importlib.util.spec_from_file_location("adapter_resolver", ADAPTERS / "resolve.py")
resolver = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(resolver)


class AdapterResolverTests(unittest.TestCase):
    def adapter(self, name: str) -> dict:
        return json.loads((ADAPTERS / name).read_text(encoding="utf-8"))

    def test_safe_default_and_high_autonomy_do_not_escalate(self):
        self.assertEqual(resolver.resolve_execution(), {"requested":"protected_manual", "source":"safe_default"})
        # Autonomy and consumption are deliberately not resolver inputs.
        self.assertEqual(resolver.resolve_preset(project="economy"), {"preset":"economy", "source":"project"})
        self.assertEqual(resolver.resolve_execution()["requested"], "protected_manual")

    def test_task_local_and_preset_precedence_are_independent(self):
        local = {"schema":resolver.OVERRIDE_SCHEMA, "profile":"protected_auto"}
        self.assertEqual(resolver.resolve_execution(local=local)["source"], "local")
        self.assertEqual(resolver.resolve_execution(task="protected_manual", local=local)["source"], "task")
        self.assertEqual(resolver.resolve_preset(task="standard", local="economy", project="economy")["source"], "task")
        self.assertEqual(resolver.parse_preset_override({"schema":resolver.PRESET_OVERRIDE_SCHEMA,"preset":"economy"}),"economy")

    def test_full_access_requires_explicit_risk_acknowledgement(self):
        with self.assertRaisesRegex(ValueError, "risk acknowledgement"):
            resolver.resolve_execution(local={"schema":resolver.OVERRIDE_SCHEMA, "profile":"full_access"})
        with self.assertRaisesRegex(ValueError, "risk acknowledgement"):
            resolver.resolve_execution(task="full_access")
        self.assertEqual(resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)["requested"], "full_access")

    def test_codex_mappings_are_distinct_and_unobserved_is_not_applied(self):
        adapter = self.adapter("codex.json")
        actions = {}
        for profile in resolver.PROFILES:
            resolved = resolver.resolve_execution(task=profile, task_risk_acknowledged=profile == "full_access")
            result = resolver.map_request(adapter, "cli", resolved)
            self.assertEqual(result["status"], "unknown" if profile == "protected_auto" else "supported")
            self.assertIsNone(result["effective"])
            self.assertFalse(result["applied"])
            actions[profile] = result["native_action"]
        self.assertEqual(len({json.dumps(x, sort_keys=True) for x in actions.values()}), 3)
        self.assertEqual(actions["protected_manual"]["settings_patch"]["approvals_reviewer"], "user")
        self.assertEqual(actions["protected_auto"]["settings_patch"]["approvals_reviewer"], "auto_review")
        self.assertEqual(actions["protected_auto"]["cli_args"],
                         ["--sandbox", "workspace-write", "--ask-for-approval", "on-request"])
        self.assertNotIn("--approve-for-me", actions["protected_auto"]["cli_args"])
        self.assertEqual(actions["full_access"]["settings_patch"]["sandbox_mode"], "danger-full-access")

    def test_codex_auto_requires_observed_capability_and_matching_effective_profile(self):
        adapter = self.adapter("codex.json")
        requested = resolver.resolve_execution(task="protected_auto")
        base = {"surface":"cli", "status":"supported", "effective":"protected_auto"}

        # A newer version label, or even an observed effective label, cannot prove capability.
        unproven = resolver.map_request(adapter, "cli", requested, observation={
            **base, "client_version":"0.155.0-alpha.16.3"})
        self.assertEqual((unproven["status"], unproven["effective"], unproven["applied"]),
                         ("unknown", None, False))
        self.assertIn("approvals_reviewer", unproven["reason"])
        no_surface = resolver.map_request(adapter, "cli", requested, observation={
            "status":"supported", "effective":"protected_auto",
            "capabilities":{"approvals_reviewer_auto_review":True}})
        self.assertEqual((no_surface["status"], no_surface["effective"]), ("unknown", None))

        unsupported = resolver.map_request(adapter, "cli", requested, observation={
            **base, "client_version":"0.144.0-alpha.4",
            "capabilities":{"approvals_reviewer_auto_review":False}})
        self.assertEqual((unsupported["status"], unsupported["effective"], unsupported["applied"]),
                         ("unsupported", None, False))
        supported = resolver.map_request(adapter, "cli", requested, observation={
            **base, "capabilities":{"approvals_reviewer_auto_review":True}})
        self.assertEqual((supported["status"], supported["effective"], supported["applied"]),
                         ("supported", "protected_auto", True))

        for observed_effective in ("full_access", "protected_manual"):
            mismatched = resolver.map_request(adapter, "cli", requested, observation={
                **base, "effective":observed_effective,
                "capabilities":{"approvals_reviewer_auto_review":True}})
            self.assertEqual((mismatched["status"], mismatched["effective"], mismatched["applied"]),
                             ("unknown", None, False))

        blocked = resolver.map_request(adapter, "cli", requested,
                                       observation={**base,"capabilities":{"approvals_reviewer_auto_review":True}},
                                       managed_policy={"allowed_profiles":["protected_manual"]})
        self.assertEqual((blocked["status"], blocked["effective"], blocked["applied"]),
                         ("unsupported", None, False))

    def test_codex_manual_and_full_access_do_not_require_auto_review(self):
        adapter = self.adapter("codex.json")
        manual = resolver.map_request(adapter, "cli", resolver.resolve_execution(task="protected_manual"),
                                      observation={"surface":"cli", "status":"supported",
                                                   "effective":"protected_manual"})
        self.assertEqual((manual["status"], manual["effective"], manual["applied"]),
                         ("supported", "protected_manual", True))
        self.assertEqual(manual["native_action"]["settings_patch"]["approvals_reviewer"], "user")
        full = resolver.map_request(adapter, "cli",
                                    resolver.resolve_execution(task="full_access", task_risk_acknowledged=True),
                                    observation={"surface":"cli", "status":"supported", "effective":"full_access"})
        self.assertEqual((full["status"], full["effective"], full["applied"]),
                         ("supported", "full_access", True))

    def test_only_the_requested_effective_profile_can_be_applied(self):
        for adapter_name in ("codex.json", "claude-code.json"):
            adapter = self.adapter(adapter_name)
            for requested_profile in resolver.PROFILES:
                requested = resolver.resolve_execution(
                    task=requested_profile,
                    task_risk_acknowledged=requested_profile == "full_access")
                for observed_profile in resolver.PROFILES:
                    with self.subTest(adapter=adapter["id"], requested=requested_profile,
                                      observed=observed_profile):
                        capabilities = {}
                        if adapter["id"] == "codex" and requested_profile == "protected_auto":
                            capabilities["approvals_reviewer_auto_review"] = True
                        if adapter["id"] == "claude_code" and requested_profile == "full_access":
                            capabilities.update(approval_bypass=True, filesystem_unrestricted=True,
                                                network_unrestricted=True)
                        result = resolver.map_request(adapter, "cli", requested, observation={
                            "surface": "cli", "status": "supported", "effective": observed_profile,
                            "capabilities": capabilities})
                        matches = observed_profile == requested_profile
                        self.assertEqual(result["applied"], matches)
                        self.assertEqual(result["effective"], requested_profile if matches else None)
                        self.assertEqual(result["status"], "supported" if matches else "unknown")
                        if not matches:
                            self.assertIn(observed_profile, result["reason"])
                            self.assertIn(requested_profile, result["reason"])

    def test_unsupported_observation_cannot_claim_applied_profile(self):
        adapter = self.adapter("codex.json")
        requested = resolver.resolve_execution(task="protected_manual")
        result = resolver.map_request(adapter, "cli", requested, observation={
            "surface": "cli", "status": "unsupported", "effective": "protected_manual"})
        self.assertEqual((result["status"], result["effective"], result["applied"]),
                         ("unsupported", None, False))

    def test_claude_auto_unknown_never_falls_through(self):
        adapter = self.adapter("claude-code.json")
        requested = resolver.resolve_execution(task="protected_auto")
        result = resolver.map_request(adapter, "cli", requested)
        self.assertEqual((result["requested"], result["effective"], result["status"]),
                         ("protected_auto", None, "unknown"))
        self.assertNotIn("dangerously-skip-permissions", result["native_action"]["cli_args"])
        mismatched = resolver.map_request(adapter,"cli",requested,
            observation={"surface":"cli","status":"supported","effective":"full_access"})
        self.assertEqual((mismatched["status"],mismatched["effective"],mismatched["applied"]),
                         ("unknown",None,False))

    def test_observation_and_managed_policy_are_reported(self):
        requested = resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)
        blocked = resolver.map_request(self.adapter("codex.json"), "cli", requested,
                                       managed_policy={"allowed_profiles":["protected_manual"]})
        self.assertEqual((blocked["status"], blocked["effective"]), ("unsupported", None))
        observed = resolver.map_request(self.adapter("codex.json"), "cli", requested,
                                        observation={"status":"supported", "effective":"full_access"})
        self.assertTrue(observed["applied"])

    def test_claude_full_access_requires_bypass_and_unrestricted_boundary(self):
        adapter = self.adapter("claude-code.json")
        requested = resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)
        base = {"surface":"cli", "status":"supported", "effective":"full_access"}
        for capabilities, missing in (
            ({"approval_bypass":True}, "filesystem_unrestricted"),
            ({"filesystem_unrestricted":True,"network_unrestricted":True}, "approval_bypass"),
            ({"approval_bypass":True,"filesystem_unrestricted":True}, "network_unrestricted"),
        ):
            result = resolver.map_request(adapter,"cli",requested,
                                          observation={**base,"capabilities":capabilities})
            self.assertEqual((result["status"],result["effective"],result["applied"]),
                             ("unknown",None,False))
            self.assertIn(missing,result["reason"])
        result = resolver.map_request(adapter,"cli",requested,observation={**base,"capabilities":{
            "approval_bypass":True,"filesystem_unrestricted":True,"network_unrestricted":True}})
        self.assertEqual((result["status"],result["effective"],result["applied"]),
                         ("supported","full_access",True))
        no_surface = resolver.map_request(adapter,"cli",requested,observation={
            "status":"supported","effective":"full_access","capabilities":{
                "approval_bypass":True,"filesystem_unrestricted":True,"network_unrestricted":True}})
        self.assertEqual((no_surface["status"],no_surface["effective"],no_surface["applied"]),
                         ("unknown",None,False))
        self.assertIn("observed surface",no_surface["reason"])
        self.assertFalse(resolver.map_request(adapter,"cli",requested)["applied"])
        blocked = resolver.map_request(adapter,"cli",requested,observation={**base,"capabilities":{
            "approval_bypass":True,"filesystem_unrestricted":True,"network_unrestricted":True}},
            managed_policy={"allowed_profiles":["protected_manual"]})
        self.assertEqual((blocked["status"],blocked["effective"],blocked["applied"]),
                         ("unsupported",None,False))

    def test_clear_override_returns_to_safe_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / ".local" / "config" / "execution-profile.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps({"schema":resolver.OVERRIDE_SCHEMA,"profile":"protected_auto"}), encoding="utf-8")
            self.assertTrue(resolver.clear_local_override(root))
            self.assertFalse(target.exists())
            self.assertEqual(resolver.resolve_execution()["requested"], "protected_manual")
            preset = root / ".local" / "config" / "preset.json"
            preset.write_text(json.dumps({"schema":resolver.PRESET_OVERRIDE_SCHEMA,"preset":"economy"}),encoding="utf-8")
            self.assertTrue(resolver.clear_local_preset(root))
            self.assertFalse(preset.exists())

    def test_linked_local_override_parents_are_rejected_without_removing_other_files(self):
        for linked_parent in (".local", ".local/config"):
            for filename, path_for, clear in (
                ("execution-profile.json", resolver.local_override_path, resolver.clear_local_override),
                ("preset.json", resolver.local_preset_path, resolver.clear_local_preset),
            ):
                with self.subTest(parent=linked_parent, filename=filename), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    other = root / "tracked"
                    destination = other / "config" if linked_parent == ".local" else other
                    destination.mkdir(parents=True)
                    sentinel = destination / filename
                    sentinel.write_bytes(b"owner data")
                    link = root / linked_parent
                    if linked_parent == ".local/config":
                        link.parent.mkdir()
                    if os.name == "nt":
                        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J",
                                        str(link), str(destination)], check=True, capture_output=True)
                    else:
                        link.symlink_to(destination, target_is_directory=True)
                    try:
                        with self.assertRaisesRegex(ValueError, "[Uu]nsafe|[Ll]ink"):
                            path_for(root)
                        with self.assertRaisesRegex(ValueError, "[Uu]nsafe|[Ll]ink"):
                            clear(root)
                        self.assertEqual(sentinel.read_bytes(), b"owner data")
                    finally:
                        if link.is_symlink():
                            link.unlink()
                        elif os.name == "nt" and link.is_junction():
                            os.rmdir(link)

    def test_invalid_local_override_leaf_never_becomes_an_absent_default(self):
        for filename, path_for in (
            ("execution-profile.json", resolver.local_override_path),
            ("preset.json", resolver.local_preset_path),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                target = config / filename
                target.mkdir()
                with self.assertRaisesRegex(ValueError, "regular"):
                    path_for(root)
                target.rmdir()
                target.write_bytes(b"x" * (resolver.MAX_LOCAL_OVERRIDE_BYTES + 1))
                with self.assertRaisesRegex(ValueError, "size limit"):
                    path_for(root)
                target.unlink()
                if os.name != "nt":
                    target.symlink_to(config / "missing.json")
                    with self.assertRaisesRegex(ValueError, "regular"):
                        path_for(root)
                    target.unlink()
                    os.mkfifo(target)
                    with self.assertRaisesRegex(ValueError, "regular"):
                        path_for(root)

    def test_clear_rejects_parent_replaced_after_path_validation(self):
        for filename, clear in (
            ("execution-profile.json", resolver.clear_local_override),
            ("preset.json", resolver.clear_local_preset),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
                root = Path(project)
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                (config / filename).write_bytes(b"local override")
                external = Path(outside)
                sentinel = external / filename
                sentinel.write_bytes(b"external owner data")
                displaced = root / "displaced-config"
                original_path = resolver._local_config_path
                swapped = False

                def swap_after_validation(project_root: Path, name: str) -> Path:
                    nonlocal swapped
                    target = original_path(project_root, name)
                    if not swapped:
                        config.rename(displaced)
                        if os.name == "nt":
                            subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J",
                                            str(config), str(external)], check=True, capture_output=True)
                        else:
                            config.symlink_to(external, target_is_directory=True)
                        swapped = True
                    return target

                try:
                    with mock.patch.object(resolver, "_local_config_path", side_effect=swap_after_validation):
                        with self.assertRaises((ValueError, OSError)):
                            clear(root)
                    self.assertTrue(swapped)
                    self.assertEqual(sentinel.read_bytes(), b"external owner data")
                    self.assertEqual((displaced / filename).read_bytes(), b"local override")
                finally:
                    if config.is_symlink():
                        config.unlink()
                    elif os.name == "nt" and config.is_junction():
                        os.rmdir(config)

    @unittest.skipUnless(os.name == "nt", "Windows native helper is required")
    def test_materialized_resolver_uses_adjacent_windows_helper_for_clear(self):
        helper = HERE.parent / "upgrade" / "_windows_mutation.py"
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            materialized = base / "materialized"
            materialized.mkdir()
            copied_resolver = materialized / "resolve.py"
            shutil.copyfile(ADAPTERS / "resolve.py", copied_resolver)
            shutil.copyfile(helper, materialized / "_windows_mutation.py")
            copied_spec = importlib.util.spec_from_file_location("materialized_resolver", copied_resolver)
            copied = importlib.util.module_from_spec(copied_spec)
            assert copied_spec.loader
            copied_spec.loader.exec_module(copied)

            project = base / "project"
            config = project / ".local" / "config"
            config.mkdir(parents=True)
            for filename, clear in (
                ("execution-profile.json", copied.clear_local_override),
                ("preset.json", copied.clear_local_preset),
            ):
                with self.subTest(filename=filename):
                    target = config / filename
                    target.write_bytes(b"local override")
                    self.assertTrue(clear(project))
                    self.assertFalse(target.exists())

            (materialized / "_windows_mutation.py").unlink()
            missing = config / "execution-profile.json"
            missing.write_bytes(b"local override")
            with self.assertRaisesRegex(OSError, "Windows native mutation helper"):
                copied.clear_local_override(project)
            self.assertEqual(missing.read_bytes(), b"local override")


if __name__ == "__main__":
    unittest.main()
