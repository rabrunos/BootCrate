"""Regression tests for the validator and scenario grader; no model API calls."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import tempfile
import validate as v

spec = importlib.util.spec_from_file_location("evaluate", v.BOOT / "evals/evaluate.py")
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)
verify_spec = importlib.util.spec_from_file_location("verify_materialized", v.BOOT / "validation/verify-materialized.py")
verify_materialized = importlib.util.module_from_spec(verify_spec)
verify_spec.loader.exec_module(verify_materialized)


class ValidationTests(unittest.TestCase):
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
        p = v.load_json(v.ROOT / "docs/.ai/project-profile.json")
        p["project"]={"name":"Example", "kind":"static", "summary":"Synthetic fixture"}
        p["versioning"].update(canonical_source="VERSION",format="project convention")
        p["security"].update(exposure="local",control_map="docs/.ai/SECURITY_BASELINE.md")
        v.materialized_profile(p)
        p["security"]["exposure"]="unknown"
        with self.assertRaises(ValueError): v.materialized_profile(p)

    def test_distribution_requires_real_unique_targets(self):
        p=v.load_json(v.ROOT/"docs/.ai/project-profile.json")
        p["project"]={"name":"Example","kind":"static","summary":"Synthetic fixture"}
        p["versioning"].update(canonical_source="VERSION",format="native")
        p["security"].update(exposure="local",control_map="docs/.ai/SECURITY_BASELINE.md")
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
            (root/"docs/.ai").mkdir(parents=True)
            (root/"PROJECT_GUIDE.md").write_text("# Project Guide\nStable downstream context.\n")
            (root/"README.md").write_text("# Example\n")
            (root/"VERSION").write_text("1.0\n")
            (root/"docs/.ai/SECURITY_BASELINE.md").write_text("# Controls\n")
            (root/"AGENTS.md").write_text("# Codex rules\n")
            (root/"CLAUDE.md").write_text("# Claude rules\n")
            p=v.load_json(v.ROOT/"docs/.ai/project-profile.json")
            p["project"]={"name":"Example","kind":"static","summary":"Synthetic fixture"}
            p["versioning"].update(canonical_source="VERSION",format="project convention")
            p["security"].update(exposure="local",control_map="docs/.ai/SECURITY_BASELINE.md")
            profile=root/"docs/.ai/project-profile.json"
            profile.write_text(json.dumps(p))
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


if __name__ == "__main__": unittest.main()
