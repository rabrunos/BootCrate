from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
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

    def test_git_tracked_local_overrides_are_never_consumed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            subprocess.run(["git","init","-q",str(root)],check=True)
            (root/".gitignore").write_text(".local/\n",encoding="utf-8")
            config=root/".local/config";config.mkdir(parents=True)
            execution=config/"execution-profile.json"
            execution.write_text(json.dumps({"schema":resolver.OVERRIDE_SCHEMA,
                                             "profile":"full_access","risk_acknowledged":True}),
                                 encoding="utf-8")
            ignored=subprocess.run(["git","check-ignore","--no-index","--quiet","--",
                                    str(execution.relative_to(root))],cwd=root)
            self.assertEqual(ignored.returncode,0)
            self.assertEqual(resolver.resolve_execution(
                local=resolver._load_local_config(root,execution.name)),
                {"requested":"full_access","source":"local"})
            relative=str(execution.relative_to(root))
            subprocess.run(["git","add","-f","--",relative],cwd=root,check=True,capture_output=True)
            self.assertTrue(execution.is_file())
            with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                resolver._load_local_config(root,execution.name)
            execution.write_text(json.dumps({"schema":resolver.OVERRIDE_SCHEMA,
                                             "profile":"protected_auto"}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                resolver._load_local_config(root,execution.name)
            task=subprocess.run([sys.executable,str(ADAPTERS/"resolve.py"),
                                 "--adapter",str(ADAPTERS/"codex.json"),"--surface","cli",
                                 "--project-root",str(root),"--task-profile","full_access",
                                 "--acknowledge-full-access-risk"],
                                capture_output=True,text=True,check=True,timeout=10)
            self.assertEqual(json.loads(task.stdout)["execution"]["source"],"task")
            subprocess.run(["git","rm","--cached","-f","--",relative],cwd=root,check=True,capture_output=True)
            self.assertTrue(execution.is_file())
            self.assertEqual(resolver.resolve_execution(
                local=resolver._load_local_config(root,execution.name))["requested"],
                "protected_auto")
            preset=config/"preset.json"
            preset.write_text(json.dumps({"schema":resolver.PRESET_OVERRIDE_SCHEMA,
                                          "preset":"economy"}),encoding="utf-8")
            self.assertEqual(resolver.parse_preset_override(
                resolver._load_local_config(root,preset.name)),"economy")
            subprocess.run(["git","add","-f","--",str(preset.relative_to(root))],
                           cwd=root,check=True,capture_output=True)
            with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                resolver._load_local_config(root,preset.name)
            subprocess.run(["git","rm","--cached","--",str(preset.relative_to(root))],
                           cwd=root,check=True,capture_output=True)
            self.assertEqual(resolver.parse_preset_override(
                resolver._load_local_config(root,preset.name)),"economy")

    def test_case_variant_tracked_local_overrides_are_rejected(self):
        for filename,payload in (("execution-profile.json",
                                 {"schema":resolver.OVERRIDE_SCHEMA,"profile":"full_access",
                                  "risk_acknowledged":True}),
                                 ("preset.json",{"schema":resolver.PRESET_OVERRIDE_SCHEMA,
                                                 "preset":"economy"})):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                subprocess.run(["git","init","-q",str(root)],check=True)
                target=root/".LOCAL/config"/filename;target.parent.mkdir(parents=True)
                target.write_text(json.dumps(payload),encoding="utf-8")
                if os.name=="nt":
                    self.assertEqual(resolver._load_local_config(root,filename),payload)
                subprocess.run(["git","add","-f","--",str(target.relative_to(root))],
                               cwd=root,check=True,capture_output=True)
                tracked=subprocess.check_output(["git","ls-files","-z"],cwd=root)
                self.assertIn((".LOCAL/config/"+filename).encode("ascii"),tracked.split(b"\0"))
                with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                    resolver._load_local_config(root,filename)

    def test_nested_git_project_rejects_tracked_local_overrides(self):
        for filename,payload in (("execution-profile.json",
                                 {"schema":resolver.OVERRIDE_SCHEMA,"profile":"full_access",
                                  "risk_acknowledged":True}),
                                 ("preset.json",{"schema":resolver.PRESET_OVERRIDE_SCHEMA,
                                                 "preset":"economy"})):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as directory:
                checkout=Path(directory)
                subprocess.run(["git","init","-q",str(checkout)],check=True)
                root=checkout/"project";config=root/".local/config";config.mkdir(parents=True)
                (root/".gitignore").write_text(".local/\n",encoding="utf-8")
                target=config/filename;target.write_text(json.dumps(payload),encoding="utf-8")
                self.assertEqual(resolver._load_local_config(root,filename),payload)
                relative=str(target.relative_to(checkout))
                subprocess.run(["git","add","-f","--",relative],cwd=checkout,
                               check=True,capture_output=True)
                with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                    resolver._load_local_config(root,filename)
                clear=(resolver.clear_local_override if filename=="execution-profile.json"
                       else resolver.clear_local_preset)
                with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                    clear(root)
                self.assertEqual(json.loads(target.read_text(encoding="utf-8")),payload)
                subprocess.run(["git","rm","--cached","-f","--",relative],cwd=checkout,
                               check=True,capture_output=True)
                self.assertEqual(resolver._load_local_config(root,filename),payload)

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
        for profile in resolver.PROFILES:
            for invalid in ("yes", 1, None, [], {}):
                with self.subTest(profile=profile, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, "risk acknowledgement"):
                        resolver.resolve_execution(task=profile, task_risk_acknowledged=invalid)
        self.assertEqual(resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)["requested"], "full_access")

    def test_local_acknowledgement_type_matches_javascript_contract(self):
        for profile in resolver.PROFILES:
            for invalid in ("yes", 1, None, [], {}):
                with self.subTest(profile=profile, invalid=invalid):
                    with self.assertRaisesRegex(ValueError, "risk acknowledgement"):
                        resolver.parse_execution_override({"schema":resolver.OVERRIDE_SCHEMA,
                                                           "profile":profile,
                                                           "risk_acknowledged":invalid})
        for profile in ("protected_manual", "protected_auto"):
            for acknowledged in (False, True):
                self.assertEqual(resolver.parse_execution_override(
                    {"schema":resolver.OVERRIDE_SCHEMA, "profile":profile,
                     "risk_acknowledged":acknowledged}), profile)
        self.assertEqual(resolver.parse_execution_override(
            {"schema":resolver.OVERRIDE_SCHEMA, "profile":"full_access",
             "risk_acknowledged":True}), "full_access")

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
        for profile in ("protected_manual", "protected_auto"):
            patch=actions[profile]["settings_patch"]
            self.assertEqual(patch["sandbox_workspace_write"],
                             {"network_access":False,"writable_roots":[]})
            self.assertEqual(patch["shell_environment_policy"],
                             {"inherit":"core","ignore_default_excludes":False})
        self.assertEqual(actions["protected_auto"]["cli_args"],
                         ["--sandbox", "workspace-write", "--ask-for-approval", "on-request"])
        self.assertNotIn("--approve-for-me", actions["protected_auto"]["cli_args"])
        self.assertEqual(actions["full_access"]["settings_patch"]["sandbox_mode"], "danger-full-access")

    def test_codex_auto_requires_observed_capability_and_matching_effective_profile(self):
        adapter = self.adapter("codex.json")
        requested = resolver.resolve_execution(task="protected_auto")
        base = {"executor":"codex", "surface":"cli", "status":"supported", "effective":"protected_auto"}

        # A newer version label, or even an observed effective label, cannot prove capability.
        unproven = resolver.map_request(adapter, "cli", requested, observation={
            **base, "client_version":"0.155.0-alpha.16.3"})
        self.assertEqual((unproven["status"], unproven["effective"], unproven["applied"]),
                         ("unknown", None, False))
        self.assertIn("approvals_reviewer", unproven["reason"])
        no_surface = resolver.map_request(adapter, "cli", requested, observation={
            "executor":"codex", "status":"supported", "effective":"protected_auto",
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
                                      observation={"executor":"codex", "surface":"cli", "status":"supported",
                                                   "effective":"protected_manual"})
        self.assertEqual((manual["status"], manual["effective"], manual["applied"]),
                         ("supported", "protected_manual", True))
        self.assertEqual(manual["native_action"]["settings_patch"]["approvals_reviewer"], "user")
        full = resolver.map_request(adapter, "cli",
                                    resolver.resolve_execution(task="full_access", task_risk_acknowledged=True),
                                    observation={"executor":"codex", "surface":"cli", "status":"supported", "effective":"full_access"})
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
                            "executor": adapter["id"], "surface": "cli", "status": "supported", "effective": observed_profile,
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
            "executor":"codex", "surface": "cli", "status": "unsupported", "effective": "protected_manual"})
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
            observation={"executor":"claude_code","surface":"cli","status":"supported","effective":"full_access"})
        self.assertEqual((mismatched["status"],mismatched["effective"],mismatched["applied"]),
                         ("unknown",None,False))

    def test_claude_protected_patches_include_credential_denials(self):
        adapter=self.adapter("claude-code.json")
        expected={"Read(./.env)","Read(./.env.*)","Read(./**/.env)",
                  "Read(./**/.env.*)","Read(./**/secrets.*)",
                  "Read(./**/credentials.*)","Read(./**/*.key)",
                  "Read(./**/*.p12)","Read(./**/*.pfx)"}
        for profile in ("protected_manual","protected_auto"):
            with self.subTest(profile=profile):
                patch=resolver.map_request(adapter,"cli",resolver.resolve_execution(task=profile))[
                    "native_action"]["settings_patch"]
                self.assertEqual(set(patch["permissions"]["deny"]),expected)
                self.assertEqual(len(patch["permissions"]["deny"]),len(expected))
                self.assertTrue(patch["sandbox"]["enabled"])

    def test_observation_and_managed_policy_are_reported(self):
        requested = resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)
        blocked = resolver.map_request(self.adapter("codex.json"), "cli", requested,
                                       managed_policy={"allowed_profiles":["protected_manual"]})
        self.assertEqual((blocked["status"], blocked["effective"]), ("unsupported", None))
        observed = resolver.map_request(self.adapter("codex.json"), "cli", requested,
                                        observation={"executor":"codex", "surface":"cli", "status":"supported", "effective":"full_access"})
        self.assertTrue(observed["applied"])

    def test_observation_must_identify_the_requested_surface(self):
        requested = resolver.resolve_execution(task="protected_manual")
        for adapter_name in ("codex.json", "claude-code.json"):
            adapter = self.adapter(adapter_name)
            for surface in ("cli", "ide"):
                with self.subTest(adapter=adapter_name, surface=surface):
                    unscoped = resolver.map_request(adapter, surface, requested, observation={
                        "executor":adapter["id"], "status":"supported", "effective":"protected_manual"})
                    self.assertEqual((unscoped["status"], unscoped["effective"], unscoped["applied"]),
                                     ("unknown", None, False))
                    self.assertIn("observed surface", unscoped["reason"])
                    other = "ide" if surface == "cli" else "cli"
                    with self.assertRaisesRegex(ValueError, "another surface"):
                        resolver.map_request(adapter, surface, requested, observation={
                            "executor":adapter["id"], "surface":other, "status":"supported", "effective":"protected_manual"})

    def test_observation_must_identify_the_requested_executor(self):
        requested = resolver.resolve_execution(task="protected_manual")
        for adapter_name, other_executor in (("codex.json", "claude_code"),
                                             ("claude-code.json", "codex")):
            adapter = self.adapter(adapter_name)
            with self.subTest(adapter=adapter["id"]):
                valid = resolver.map_request(adapter, "cli", requested, observation={
                    "executor":adapter["id"], "surface":"cli", "status":"supported",
                    "effective":"protected_manual"})
                self.assertTrue(valid["applied"])
                unbound = resolver.map_request(adapter, "cli", requested, observation={
                    "surface":"cli", "status":"supported", "effective":"protected_manual"})
                self.assertEqual((unbound["status"], unbound["effective"], unbound["applied"]),
                                 ("unknown", None, False))
                self.assertIn("observed executor", unbound["reason"])
                with self.assertRaisesRegex(ValueError, "another executor"):
                    resolver.map_request(adapter, "cli", requested, observation={
                        "executor":other_executor, "surface":"cli", "status":"supported",
                        "effective":"protected_manual"})

    def test_claude_full_access_requires_bypass_and_unrestricted_boundary(self):
        adapter = self.adapter("claude-code.json")
        requested = resolver.resolve_execution(task="full_access", task_risk_acknowledged=True)
        base = {"executor":"claude_code", "surface":"cli", "status":"supported", "effective":"full_access"}
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
            "executor":"claude_code","status":"supported","effective":"full_access","capabilities":{
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

    def test_tracked_local_overrides_cannot_be_cleared(self):
        for filename, clear in (
            ("execution-profile.json", resolver.clear_local_override),
            ("preset.json", resolver.clear_local_preset),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run(["git", "init", "-q", str(root)], check=True)
                (root / ".gitignore").write_text(".local/\n", encoding="utf-8")
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                target = config / filename
                target.write_bytes(b"tracked owner content")
                relative = str(target.relative_to(root))
                subprocess.run(["git", "add", "-f", "--", relative], cwd=root,
                               check=True, capture_output=True)

                with self.assertRaisesRegex(ValueError, "Tracked machine-local configuration"):
                    clear(root)
                command = [sys.executable, str(ADAPTERS / "resolve.py"),
                           "--adapter", str(ADAPTERS / "codex.json"), "--surface", "cli",
                           "--project-root", str(root),
                           "--task-profile", "full_access", "--acknowledge-full-access-risk",
                           "--task-preset", "standard",
                           "--clear-local" if filename == "execution-profile.json" else "--clear-local-preset"]
                result = subprocess.run(command, capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Tracked machine-local configuration", result.stderr)
                self.assertEqual(target.read_bytes(), b"tracked owner content")
                self.assertEqual(list(config.glob(".clear-*")), [])

                subprocess.run(["git", "rm", "--cached", "-f", "--", relative], cwd=root,
                               check=True, capture_output=True)
                self.assertTrue(clear(root))
                self.assertFalse(target.exists())

    def test_combined_clear_preflights_both_tracking_states(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            config = root / ".local" / "config"
            config.mkdir(parents=True)
            execution = config / "execution-profile.json"
            preset = config / "preset.json"
            execution.write_bytes(b"untracked owner content")
            preset.write_bytes(b"tracked owner content")
            subprocess.run(["git", "add", "-f", "--", str(preset.relative_to(root))],
                           cwd=root, check=True, capture_output=True)
            result = subprocess.run([sys.executable, str(ADAPTERS / "resolve.py"),
                                     "--adapter", str(ADAPTERS / "codex.json"),
                                     "--surface", "cli", "--project-root", str(root),
                                     "--task-profile", "full_access", "--acknowledge-full-access-risk",
                                     "--task-preset", "standard", "--clear-local",
                                     "--clear-local-preset"],
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Tracked machine-local configuration", result.stderr)
            self.assertEqual(execution.read_bytes(), b"untracked owner content")
            self.assertEqual(preset.read_bytes(), b"tracked owner content")
            self.assertEqual(list(config.glob(".clear-*")), [])

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

    def test_clear_preserves_owner_leaf_replaced_after_validation(self):
        for filename, clear in (
            ("execution-profile.json", resolver.clear_local_override),
            ("preset.json", resolver.clear_local_preset),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                target = config / filename
                displaced = config / (filename + ".previous")
                target.write_bytes(b"validated override")
                original_unlink = resolver._unlink_local_file

                def replace_before_unlink(path: Path, expected_identity: tuple[int, int]) -> None:
                    path.rename(displaced)
                    path.write_bytes(b"new owner override")
                    original_unlink(path, expected_identity)

                with mock.patch.object(resolver, "_unlink_local_file", side_effect=replace_before_unlink):
                    with self.assertRaisesRegex(ValueError, "changed"):
                        clear(root)
                self.assertEqual(target.read_bytes(), b"new owner override")
                self.assertEqual(displaced.read_bytes(), b"validated override")

    @unittest.skipUnless(os.name == "posix" and sys.platform == "linux",
                         "Linux renameat2 is required")
    def test_clear_quarantines_verified_leaf_without_unlink_race(self):
        for filename, clear in (
            ("execution-profile.json", resolver.clear_local_override),
            ("preset.json", resolver.clear_local_preset),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                target = config / filename
                target.write_bytes(b"validated override")
                self.assertTrue(clear(root))
                self.assertFalse(target.exists())
                quarantined = list(config.glob(".clear-*"))
                self.assertEqual(len(quarantined), 1)
                self.assertEqual(quarantined[0].read_bytes(), b"validated override")

    @unittest.skipUnless(os.name == "posix" and sys.platform == "linux",
                         "Linux renameat2 is required")
    def test_clear_restores_leaf_swapped_immediately_before_displacement(self):
        for filename, clear in (
            ("execution-profile.json", resolver.clear_local_override),
            ("preset.json", resolver.clear_local_preset),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                target = config / filename
                previous = config / (filename + ".previous")
                target.write_bytes(b"validated override")
                original_move = resolver._rename_local_noreplace
                swapped = False

                def replace_before_move(parent_fd: int, source: str, destination: str) -> None:
                    nonlocal swapped
                    if source == filename and not swapped:
                        target.rename(previous)
                        target.write_bytes(b"new owner override")
                        swapped = True
                    original_move(parent_fd, source, destination)

                with mock.patch.object(resolver, "_rename_local_noreplace", side_effect=replace_before_move):
                    with self.assertRaisesRegex(ValueError, "changed"):
                        clear(root)
                self.assertTrue(swapped)
                self.assertEqual(target.read_bytes(), b"new owner override")
                self.assertEqual(previous.read_bytes(), b"validated override")
                self.assertEqual(list(config.glob(".clear-*")), [])

    def test_local_reads_use_bounded_handles_after_path_validation(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(resolver._load_local_config(Path(empty), "execution-profile.json"))
            self.assertIsNone(resolver._load_local_config(Path(empty), "preset.json"))
        for filename, payload in (
            ("execution-profile.json", {"schema": resolver.OVERRIDE_SCHEMA, "profile": "protected_manual"}),
            ("preset.json", {"schema": resolver.PRESET_OVERRIDE_SCHEMA, "preset": "standard"}),
        ):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as outside:
                root = Path(project)
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                (config / filename).write_text(json.dumps(payload), encoding="utf-8")
                self.assertEqual(resolver._load_local_config(root, filename), payload)
                external = Path(outside)
                sentinel = external / filename
                sentinel.write_bytes(b"external owner bytes")
                displaced = root / "displaced-config"
                original_path = resolver._local_config_path

                def swap_after_validation(project_root: Path, name: str) -> Path:
                    target = original_path(project_root, name)
                    config.rename(displaced)
                    if os.name == "nt":
                        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J",
                                        str(config), str(external)], check=True, capture_output=True)
                    else:
                        config.symlink_to(external, target_is_directory=True)
                    return target

                try:
                    with mock.patch.object(resolver, "_local_config_path", side_effect=swap_after_validation):
                        with self.assertRaises((ValueError, OSError)):
                            resolver._load_local_config(root, filename)
                    self.assertEqual(sentinel.read_bytes(), b"external owner bytes")
                    self.assertEqual(json.loads((displaced / filename).read_text(encoding="utf-8")), payload)
                finally:
                    if config.is_symlink():
                        config.unlink()
                    elif os.name == "nt" and config.is_junction():
                        os.rmdir(config)

    def test_local_read_rejects_fifo_and_oversize_swapped_after_validation(self):
        replacements = ("oversize",) if os.name == "nt" else ("fifo", "oversize")
        for replacement in replacements:
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / ".local" / "config"
                config.mkdir(parents=True)
                target = config / "execution-profile.json"
                target.write_text(json.dumps({"schema": resolver.OVERRIDE_SCHEMA,
                                              "profile": "protected_manual"}), encoding="utf-8")
                original_path = resolver._local_config_path

                def swap_after_validation(project_root: Path, name: str) -> Path:
                    checked = original_path(project_root, name)
                    target.unlink()
                    if replacement == "fifo":
                        os.mkfifo(target)
                    else:
                        target.write_bytes(b"x" * (resolver.MAX_LOCAL_OVERRIDE_BYTES + 1))
                    return checked

                with mock.patch.object(resolver, "_local_config_path", side_effect=swap_after_validation):
                    with self.assertRaisesRegex(ValueError, "regular|size limit|read limit"):
                        resolver._load_local_config(root, "execution-profile.json")

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
            with self.assertRaisesRegex(OSError, "Windows native mutation helper"):
                copied._load_local_config(project, "execution-profile.json")
            self.assertEqual(missing.read_bytes(), b"local override")


if __name__ == "__main__":
    unittest.main()
