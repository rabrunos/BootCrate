"""Regression tests for the validator and scenario grader; no model API calls."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
from unittest.mock import patch
import validate as v

spec = importlib.util.spec_from_file_location("evaluate", v.BOOT / "evals/evaluate.py")
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)
verify_spec = importlib.util.spec_from_file_location("verify_materialized", v.BOOT / "validation/verify-materialized.py")
verify_materialized = importlib.util.module_from_spec(verify_spec)
verify_spec.loader.exec_module(verify_materialized)


class ValidationTests(unittest.TestCase):
    def test_intake_schema_requires_full_access_acknowledgement(self):
        schema=v.load_json(v.BOOT/"schemas/project-intake.schema.json")
        base={"schema":"bootcrate-project-intake/v2"}
        for profile in ("protected_manual","protected_auto"):
            v.schema_check(schema,{**base,"answers":{"execution_profile":profile}})
        with self.assertRaises(ValueError):
            v.schema_check(schema,{**base,"answers":{"execution_profile":"full_access"}})
        with self.assertRaises(ValueError):
            v.schema_check(schema,{**base,"answers":{"execution_profile":"full_access",
                                                   "full_access_acknowledgement":"yes"}})
        v.schema_check(schema,{**base,"answers":{"execution_profile":"full_access",
                                              "full_access_acknowledgement":"acknowledged"}})

    def test_repository_identity_schema_matches_shared_intake_validator(self):
        schema=v.load_json(v.BOOT/"schemas/project-intake.schema.json")
        values=["owner/repo", "owner/repo-name", "owner/.repo", "owner/.", "owner/..",
                "owner/repo.git", "owner/repo.git.git", "owner//repo", "-owner/repo",
                "owner/repo/name", "https://github.com/owner/repo"]
        script="""
const fs=require('node:fs'),vm=require('node:vm'),Core=require(process.argv[1]);
const scope={window:{}};
vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),scope);
const core=Core.create(scope.window.BOOTCRATE_QUESTIONS);
const values=JSON.parse(fs.readFileSync(0,'utf8'));
process.stdout.write(JSON.stringify(values.map(repository=>
  core.validate({schema:Core.SCHEMA,answers:{},repository}).length===0)));
"""
        result=subprocess.run(
            ["node", "-e", script, str(v.BOOT/"app/intake-core.js"), str(v.BOOT/"app/questions.js")],
            input=json.dumps(values), text=True, capture_output=True, check=True, timeout=10)
        core_results=json.loads(result.stdout)
        self.assertEqual(len(core_results),len(values))
        for repository, core_valid in zip(values, core_results):
            with self.subTest(repository=repository):
                try:
                    v.schema_check(schema,{"schema":"bootcrate-project-intake/v2", "answers":{},
                                           "repository":repository})
                    schema_valid=True
                except ValueError:
                    schema_valid=False
                self.assertEqual(schema_valid,core_valid)

    def test_command_failure_reports_bounded_stderr_tail(self):
        script="import sys; sys.stderr.write('progress\\n'*1000); sys.stderr.write('test_synthetic_failure\\nTraceback marker\\n'); sys.exit(7)"
        with self.assertRaises(ValueError) as failure:
            v.run([sys.executable,"-c",script])
        message=str(failure.exception)
        self.assertIn("exit 7",message)
        self.assertIn("test_synthetic_failure\nTraceback marker",message)
        self.assertIn("earlier stderr characters omitted",message)
        self.assertLess(len(message),9000)

    def finalize_profile(self, profile):
        profile["project"]={"name":"Example", "kind":"static", "summary":"Synthetic fixture"}
        profile["versioning"].update(
            canonical_source="VERSION",reader="plain",format="project convention",
            history_source="CHANGELOG.md",history_format="markdown-headings",mirrors=[]
        )
        profile["security"].update(exposure="local",control_map="docs/.ai/SECURITY_BASELINE.md")
        profile["workflow"]["implementation_harnesses"]=["codex"]
        return profile

    def materialized_fixture(self, root, console=False):
        for name, body in {
            "docs/.ai/SECURITY_BASELINE.md":"# Controls\n",
            "PROJECT_GUIDE.md":"# Project Guide\nStable downstream context.\n",
            "README.md":"# Example\n",
            "VERSION":"1.0\n",
            "CHANGELOG.md":"# Changelog\n\n## v1.0 — Initial\n\n- Added the synthetic fixture.\n",
            "AGENTS.md":"# Codex rules\n",
            ".codex/config.toml":'model_reasoning_effort = "high"\n'
                                  'sandbox_mode = "workspace-write"\n'
                                  'approval_policy = "on-request"\n'
                                  'approvals_reviewer = "user"\n',
        }.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body,encoding="utf-8")
        profile=self.finalize_profile(v.load_json(v.ROOT/"docs/.ai/project-profile.json"))
        profile["console"]["enabled"]=console
        path=root/"docs/.ai/project-profile.json"
        path.write_text(json.dumps(profile),encoding="utf-8")
        return profile,path

    def directory_link(self, link, target):
        try:
            link.symlink_to(target,target_is_directory=True)
        except OSError:
            if os.name!='nt':raise
            subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(link),str(target)],
                           check=True,capture_output=True)

    def test_duplicate_json_rejected(self):
        with self.assertRaises(ValueError): json.loads('{"x":1,"x":2}', object_pairs_hook=v.unique_object)

    def test_duplicate_yaml_rejected(self):
        with self.assertRaises(ValueError): v.load_yaml("x: 1\nx: 2")

    def test_explicit_unknown_and_not_applicable_intake_schema(self):
        schema=v.load_json(v.BOOT/'schemas/project-intake.schema.json')
        data=v.load_json(v.BOOT/'templates/project-intake.example.json')
        data['answer_states']={'known_risks':'unknown','must_avoid_tools':'not_applicable'}
        v.schema_check(schema,data)
        data['answer_states']['made_up_field']='unknown'
        with self.assertRaises(ValueError):v.schema_check(schema,data)

    def test_workflow_on_is_not_boolean(self):
        self.assertIn("on", v.load_yaml("on: [push]\nvalue: true"))

    def test_remote_schema_ref_rejected(self):
        with self.assertRaises(ValueError): v.local_refs_only({"$ref":"https://invalid.example/schema"})

    def test_sensitive_names(self):
        for name in [".env", ".env.production", "credentials.json", "private.key"]:
            self.assertTrue(v.sensitive_name(Path(name)))
        self.assertFalse(v.sensitive_name(Path(".env.example")))

    def test_secret_smoke_positive_and_negative(self):
        self.assertTrue(v.secret_findings("ghp_" + "A" * 36))
        self.assertTrue(v.secret_findings("-----BEGIN " + "PRIVATE KEY-----"))
        self.assertFalse(v.secret_findings("API_TOKEN=<configure locally>"))

    def test_generic_profile_is_valid_but_not_finalized(self):
        p = v.load_json(v.ROOT / "docs/.ai/project-profile.json")
        s = v.load_json(v.ROOT / "docs/.ai/schemas/project-profile.schema.json")
        v.schema_check(s,p)
        with self.assertRaises(ValueError): v.materialized_profile(p)

    def test_missing_security_profile_rejected(self):
        p = v.load_json(v.ROOT / "docs/.ai/project-profile.json");p.pop("security")
        with self.assertRaises(ValueError): v.schema_check(v.load_json(v.ROOT / "docs/.ai/schemas/project-profile.schema.json"),p)

    def test_disabled_versioning_rejected(self):
        p = v.load_json(v.ROOT / "docs/.ai/project-profile.json");p["versioning"]["required"] = False
        with self.assertRaises(ValueError): v.schema_check(v.load_json(v.ROOT / "docs/.ai/schemas/project-profile.schema.json"),p)

    def test_finalized_profile(self):
        p = self.finalize_profile(v.load_json(v.ROOT / "docs/.ai/project-profile.json"))
        v.materialized_profile(p)
        p["security"]["exposure"]="unknown"
        with self.assertRaises(ValueError): v.materialized_profile(p)

    def test_distribution_requires_real_unique_targets(self):
        p=self.finalize_profile(v.load_json(v.ROOT/"docs/.ai/project-profile.json"))
        p["distribution"]={"mode":"artifact","targets":[]}
        with self.assertRaisesRegex(ValueError,"without a destination"):v.materialized_profile(p)
        p["distribution"]["targets"]=[{"id":"release","channel":"stable","kind":"artifact"}]*2
        with self.assertRaisesRegex(ValueError,"Duplicate distribution"):v.materialized_profile(p)

    def test_scenario_rubrics(self):
        scenarios = v.load_json(v.BOOT / "evals/scenarios.json")["scenarios"]
        self.assertEqual(len(scenarios),len({s["id"] for s in scenarios}))
        for s in scenarios:
            e=s["expected"]
            c={"scenario":s["id"],"main_effort":e["main_effort"][0],"local_discovery":e["local_discovery"][0],
               "security_modules":e.get("required_modules",[]),"controls":e.get("required_controls",[]),
               "capabilities":[],"blocked_actions":e.get("required_blocked_actions",[]),
               "needs_owner_decision":e.get("needs_owner_decision",False),"rationale":"Synthetic grader fixture, not an actual model result."}
            self.assertEqual(evaluate.grade(s,c),[],s["id"])
            bad=copy.deepcopy(c);bad["blocked_actions"]=[]
            self.assertTrue(evaluate.grade(s,bad),s["id"])
            bad=copy.deepcopy(c);bad["controls"]=[]
            self.assertTrue(evaluate.grade(s,bad),s["id"])
            bad=copy.deepcopy(c);bad["capabilities"]=[c["blocked_actions"][0]]
            self.assertTrue(evaluate.grade(s,bad),s["id"])

    def test_security_downgrade_rejected(self):
        s=next(s for s in v.load_json(v.BOOT / "evals/scenarios.json")["scenarios"] if s["id"]=="saas-identity")
        e=s["expected"]
        c={"scenario":s["id"],"main_effort":"medium","local_discovery":"targeted","security_modules":e["required_modules"],
           "controls":e["required_controls"],"capabilities":[],"blocked_actions":e["required_blocked_actions"],
           "needs_owner_decision":False,"rationale":"Synthetic invalid downgrade"}
        self.assertIn("unexpected main_effort",evaluate.grade(s,c))

    def test_post_materialization_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.materialized_fixture(root)
            self.assertEqual(verify_materialized.check(root),[])
            (root/"docs/.human/bootstrap").mkdir(parents=True)
            self.assertIn("bootstrap directory remains",verify_materialized.check(root))

    def test_v3_selected_codex_config_requires_protected_manual_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            config=root/".codex/config.toml"
            self.assertEqual(verify_materialized.check(root),[])
            for content in (
                'sandbox_mode = "danger-full-access"\napproval_policy = "never"\n',
                'sandbox_mode = "workspace-write"\napproval_policy = "never"\napprovals_reviewer = "user"\n',
                'sandbox_mode = "workspace-write"\napproval_policy = "on-request"\napprovals_reviewer = "auto_review"\n',
            ):
                with self.subTest(content=content):
                    config.write_text(content,encoding="utf-8")
                    self.assertTrue(any("Codex protected manual defaults" in failure
                                        for failure in verify_materialized.check(root)))
            config.write_text('sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n'
                              'approvals_reviewer = "user"\n',encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])
            config.write_bytes(b"\xff")
            self.assertEqual(next(entry for entry in verify_materialized.inspect(root)
                                  if entry["check_id"] == "profile.finalized")["status"],"fail")

    def test_v3_selected_claude_config_requires_protected_manual_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            profile["workflow"]["implementation_harnesses"]=["codex","claude_code"]
            path.write_text(json.dumps(profile),encoding="utf-8")
            (root/"CLAUDE.md").write_text("# Claude rules\n",encoding="utf-8")
            settings=root/".claude/settings.json";settings.parent.mkdir()
            def write_settings(mode,enabled):
                settings.write_text(json.dumps({"permissions":{"defaultMode":mode},
                                                "sandbox":{"enabled":enabled}}),encoding="utf-8")
            write_settings("default",True)
            self.assertEqual(verify_materialized.check(root),[])
            for mode,enabled in (("bypassPermissions",True),("default",False)):
                with self.subTest(mode=mode,enabled=enabled):
                    write_settings(mode,enabled)
                    self.assertTrue(any("Claude protected manual defaults" in failure
                                        for failure in verify_materialized.check(root)))
            write_settings("default",True)
            self.assertEqual(verify_materialized.check(root),[])

    def test_native_default_gate_is_v3_and_selected_executor_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            claude=root/".claude/settings.json";claude.parent.mkdir()
            claude.write_text('{"permissions":{"defaultMode":"bypassPermissions"}}',encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])  # Claude is not selected.
            profile={
                "schema":"project-profile/v2",
                "project":{"name":"Legacy example","kind":"static","summary":"Synthetic fixture"},
                "owner":{"repository_language":"en","report_language":"pt-BR"},
                "workflow":{"tracking":"github_issues","primary_orchestrator":"chatgpt",
                            "fallback_planners":[],"implementation_harnesses":["codex"]},
                "versioning":{"required":True,"canonical_source":"VERSION","format":"native",
                              "target_version_in_prompt_h1":True,"target_version_in_commit":True,
                              "target_version_in_report_h1":True,"continuations_reuse_target":True},
                "security":{"exposure":"local","data_classes":[],"untrusted_inputs":[],
                            "modules":[],"control_map":"docs/.ai/SECURITY_BASELINE.md",
                            "verification_commands":[]},
            }
            path.write_text(json.dumps(profile),encoding="utf-8")
            (root/".codex/config.toml").write_text('sandbox_mode = "danger-full-access"\n'
                                                  'approval_policy = "never"\n',encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])  # v2 had no native-default contract.

    def test_materialized_profile_negative_cases(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/"docs/.ai").mkdir(parents=True)
            profile=root/"docs/.ai/project-profile.json"
            self.assertIn("project profile missing",verify_materialized.check(root))
            profile.write_text('{"schema":"project-profile/v3","schema":"project-profile/v3"}')
            self.assertTrue(any("Duplicate JSON key" in x for x in verify_materialized.check(root)))
            profile.write_text('{"schema":"project-profile/v9"}')
            self.assertIn("Unsupported project profile schema",verify_materialized.check(root))
            profile.write_text('{"project":"example"}')
            self.assertIn("Unsupported project profile schema",verify_materialized.check(root))

    def test_materialized_verifier_does_not_read_ignored_secrets(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            import subprocess
            subprocess.run(["git","init","-q",str(root)],check=True)
            (root/".gitignore").write_text(".env\n")
            (root/".env").write_text("private data is never inspected")
            tracked,untracked=v.project_inventory(root)
            self.assertNotIn(root/".env",tracked+untracked)

    def test_version_history_mirrors_and_declared_files_are_required(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            (root/"CHANGELOG.md").unlink()
            self.assertTrue(any("history" in x for x in verify_materialized.check(root)))
            (root/"CHANGELOG.md").write_text("# Changelog\n\n## v1.0 — Initial\n",encoding="utf-8")
            (root/"VERSION").write_text("")
            self.assertIn("Invalid canonical version value",verify_materialized.check(root))
            (root/"VERSION").write_text("not a version with spaces\n")
            self.assertIn("Invalid canonical version value",verify_materialized.check(root))
            (root/"VERSION").write_text("1.0\n")
            (root/"package.json").write_text('{"version":"1.1"}')
            profile["versioning"]["mirrors"]=[
                {"path":"package.json","reader":"json","value_path":"/version"}
            ]
            path.write_text(json.dumps(profile))
            self.assertTrue(any("mirror diverge" in x for x in verify_materialized.check(root)))
            profile["versioning"]["mirrors"][0]["path"]="missing.json"
            profile["validation"]["required_files"]=["docs/product-contract.md"]
            path.write_text(json.dumps(profile))
            failures=verify_materialized.check(root)
            self.assertTrue(any("version mirror" in x for x in failures))
            profile["versioning"]["mirrors"]=[];path.write_text(json.dumps(profile))
            self.assertTrue(any("declared required file" in x for x in verify_materialized.check(root)))

    def test_selected_console_requires_complete_local_dependencies(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root,console=True)
            console=root/"project-console";console.mkdir()
            (console/"index.html").write_text(
                '<!doctype html><link rel="stylesheet" href="styles.css"><script src="preset.js"></script><script src="execution-profile.js"></script><script src="console.js"></script>'
            )
            self.assertTrue(any("dependency missing" in x for x in verify_materialized.check(root)))
            for name in ("styles.css","preset.js","execution-profile.js","console.js"):(console/name).write_text("/* fixture */\n")
            self.assertEqual(verify_materialized.check(root),[])
            (console/"index.html").write_text('<!doctype html><script src="missing.js"></script>')
            self.assertTrue(any("reference missing" in x for x in verify_materialized.check(root)))

    def test_inventory_distinguishes_binary_assets_from_text_scan_limits(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            (root/"asset.bin").write_bytes(b"\0"*(2*1024*1024+1))
            self.assertEqual(verify_materialized.check(root),[])
            (root/"large.txt").write_bytes(b"x"*(2*1024*1024+1))
            results=verify_materialized.inspect(root)
            self.assertEqual(next(x for x in results if x["check_id"]=="source.inventory")["status"],"pass")
            self.assertEqual(next(x for x in results if x["check_id"]=="security.text_scan")["status"],"blocked")

    def test_inventory_limits_tracked_secret_and_external_link(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);root=home/"product";root.mkdir();self.materialized_fixture(root)
            subprocess.run(["git","init","-q",str(root)],check=True)
            (root/".env").write_text("synthetic-value")
            subprocess.run(["git","-C",str(root),"add","-f",".env"],check=True)
            self.assertTrue(any("secret-bearing filename tracked" in x for x in verify_materialized.check(root)))
            subprocess.run(["git","-C",str(root),"rm","--cached","-q",".env"],check=True)
            (root/".gitignore").write_text(".env\n")
            self.assertEqual(verify_materialized.check(root),[])
            outside=home/"outside";outside.mkdir();(outside/"private.txt").write_text("do not read")
            self.directory_link(root/"linked",outside)
            link=root/"linked"
            try:
                self.assertTrue(any("symlink/external" in x for x in verify_materialized.check(root)))
            finally:
                if link.is_symlink(): link.unlink()
                else: os.rmdir(link)  # Windows junction fallback.

        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            for index in range(3):(root/f"f{index}.bin").write_bytes(b"1234")
            with patch.object(verify_materialized,"MAX_INVENTORY_FILES",2):
                self.assertTrue(any("inventory exceeds" in x for x in verify_materialized.check(root)))
            with patch.object(verify_materialized,"MAX_INVENTORY_BYTES",8):
                self.assertTrue(any("inventory exceeds" in x for x in verify_materialized.check(root)))


if __name__ == "__main__": unittest.main()
