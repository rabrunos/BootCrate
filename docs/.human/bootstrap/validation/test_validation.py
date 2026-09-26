"""Regression tests for the validator and scenario grader; no model API calls."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
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
            ".codex/config.toml":'model_reasoning_effort = "high"\n',
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
            try:
                self.assertTrue(any("symlink/external" in x for x in verify_materialized.check(root)))
            finally:
                os.rmdir(root/"linked")

        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            for index in range(3):(root/f"f{index}.bin").write_bytes(b"1234")
            with patch.object(verify_materialized,"MAX_INVENTORY_FILES",2):
                self.assertTrue(any("inventory exceeds" in x for x in verify_materialized.check(root)))
            with patch.object(verify_materialized,"MAX_INVENTORY_BYTES",8):
                self.assertTrue(any("inventory exceeds" in x for x in verify_materialized.check(root)))


if __name__ == "__main__": unittest.main()
