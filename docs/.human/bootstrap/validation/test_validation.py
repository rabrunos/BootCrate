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
            (root/"docs/.ai/project-profile.json").write_text('{"project":"example"}')
            self.assertEqual(verify_materialized.check(root),[])
            (root/"docs/.human/bootstrap").mkdir(parents=True)
            self.assertIn("bootstrap directory remains",verify_materialized.check(root))


if __name__ == "__main__": unittest.main()
