"""Regression tests for the validator and scenario grader; no model API calls."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import tempfile
import tomllib
from unittest.mock import patch
import validate as v
from validation_core import reject_unselected_codex_config, reject_unselected_claude_config

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
                v.schema_check(schema,{**base,"answers":{"execution_profile":profile,
                                                       "full_access_acknowledgement":"acknowledged"}})
        with self.assertRaises(ValueError):
            v.schema_check(schema,{**base,"answers":{"full_access_acknowledgement":"acknowledged"}})
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
                                  'approvals_reviewer = "user"\n'
                                  '[sandbox_workspace_write]\nnetwork_access = false\n'
                                  '[shell_environment_policy]\ninherit = "core"\n'
                                  'ignore_default_excludes = false\n',
        }.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body,encoding="utf-8")
        profile=self.finalize_profile(v.load_json(v.ROOT/"docs/.ai/project-profile.json"))
        profile["console"]["enabled"]=console
        path=root/"docs/.ai/project-profile.json"
        path.write_text(json.dumps(profile),encoding="utf-8")
        return profile,path

    def test_materialized_executor_skill_sets_are_exact(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            profile["skills"]=["safe-validation"]
            path.write_text(json.dumps(profile),encoding="utf-8")
            codex=root/".agents/skills";codex.mkdir(parents=True)
            selected=codex/"safe-validation";selected.mkdir()
            (selected/"SKILL.md").write_text("# selected\n",encoding="utf-8")
            v.materialized_profile(profile,root)
            extra=codex/"unexpected";extra.mkdir()
            (extra/"SKILL.md").write_text("# unexpected\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"skills differ"):
                v.materialized_profile(profile,root)
            self.assertTrue(any("skills differ" in failure for failure in verify_materialized.check(root)))
            shutil.rmtree(extra)
            (codex/"command.py").write_text("print('synthetic')\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Unexpected executor skill-root entry"):
                v.materialized_profile(profile,root)
            (codex/"command.py").unlink()
            selected.rename(codex/"missing")
            with self.assertRaisesRegex(ValueError,"Missing selected executor skill"):
                v.materialized_profile(profile,root)
            (codex/"missing").rename(codex/"safe-validation")
            profile["skills"]=[];path.write_text(json.dumps(profile),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"skills differ"):
                v.materialized_profile(profile,root)

    def test_materialized_claude_and_codex_skill_sets_are_exact(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            profile["workflow"]["implementation_harnesses"]=["codex","claude_code"]
            profile["skills"]=["safe-validation"]
            path.write_text(json.dumps(profile),encoding="utf-8")
            (root/"CLAUDE.md").write_text("# Claude\n",encoding="utf-8")
            native=root/".claude/settings.json";native.parent.mkdir()
            native.write_text("{}",encoding="utf-8")
            for skill_root in (root/".agents/skills",root/".claude/skills"):
                selected=skill_root/"safe-validation";selected.mkdir(parents=True)
                (selected/"SKILL.md").write_text("# selected\n",encoding="utf-8")
            v.materialized_profile(profile,root)
            extra=root/".claude/skills/unexpected";extra.mkdir()
            (extra/"SKILL.md").write_text("# unexpected\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"skills differ"):
                v.materialized_profile(profile,root)
            shutil.rmtree(extra)
            link=root/".agents/skills/unexpected"
            self.directory_link(link,root/".agents/skills/safe-validation")
            try:
                with self.assertRaisesRegex(ValueError,"Unexpected executor skill-root entry"):
                    v.materialized_profile(profile,root)
            finally:
                if link.is_symlink():link.unlink()
                elif os.name=="nt" and link.is_junction():os.rmdir(link)
            v.materialized_profile(profile,root)

    def test_materialized_rejects_tracked_machine_local_overrides(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,_=self.materialized_fixture(root)
            subprocess.run(["git","init","-q",str(root)],check=True)
            (root/".gitignore").write_text(".local/\n",encoding="utf-8")
            config=root/".local/config";config.mkdir(parents=True)
            for filename in ("execution-profile.json","preset.json"):
                target=config/filename;target.write_text("{}",encoding="utf-8")
                self.assertEqual(verify_materialized.check(root),[])
                ignored=subprocess.run(["git","check-ignore","--no-index","--quiet","--",
                                        str(target.relative_to(root))],cwd=root)
                self.assertEqual(ignored.returncode,0)
                subprocess.run(["git","add","-f","--",str(target.relative_to(root))],
                               cwd=root,check=True,capture_output=True)
                with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                    v.materialized_profile(profile,root)
                self.assertTrue(any("Tracked machine-local configuration" in failure
                                    for failure in verify_materialized.check(root)))
                subprocess.run(["git","rm","--cached","-f","--",str(target.relative_to(root))],
                               cwd=root,check=True,capture_output=True)
                self.assertTrue(target.is_file())
                target.unlink()
            self.assertEqual(verify_materialized.check(root),[])

    def test_materialized_rejects_case_variant_tracked_local_overrides(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,_=self.materialized_fixture(root)
            subprocess.run(["git","init","-q",str(root)],check=True)
            for filename in ("execution-profile.json","preset.json"):
                target=root/".LOCAL/config"/filename;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text("{}",encoding="utf-8")
                subprocess.run(["git","add","-f","--",str(target.relative_to(root))],
                               cwd=root,check=True,capture_output=True)
                with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                    v.materialized_profile(profile,root)
                self.assertTrue(any("Tracked machine-local configuration" in failure
                                    for failure in verify_materialized.check(root)))
                subprocess.run(["git","rm","--cached","--",str(target.relative_to(root))],
                               cwd=root,check=True,capture_output=True)
                target.unlink()
            self.assertEqual(verify_materialized.check(root),[])

    def test_nested_git_project_rejects_tracked_local_overrides(self):
        with tempfile.TemporaryDirectory() as td:
            checkout=Path(td)
            subprocess.run(["git","init","-q",str(checkout)],check=True)
            root=checkout/"project";root.mkdir()
            profile,_=self.materialized_fixture(root)
            (root/".gitignore").write_text(".local/\n",encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])
            config=root/".local/config";config.mkdir(parents=True)
            for filename in ("execution-profile.json","preset.json"):
                target=config/filename;target.write_text("{}",encoding="utf-8")
                self.assertNotIn(target,v.project_inventory(root)[0])
                relative=str(target.relative_to(checkout))
                subprocess.run(["git","add","-f","--",relative],cwd=checkout,
                               check=True,capture_output=True)
                self.assertIn(target,v.project_inventory(root)[0])
                with self.assertRaisesRegex(ValueError,"Tracked machine-local configuration"):
                    v.materialized_profile(profile,root)
                self.assertTrue(any("Tracked machine-local configuration" in failure
                                    for failure in verify_materialized.check(root)))
                subprocess.run(["git","rm","--cached","-f","--",relative],cwd=checkout,
                               check=True,capture_output=True)
                self.assertEqual(verify_materialized.check(root),[])
                target.unlink()

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
            original = config.read_text(encoding="utf-8")
            config.write_text(original.replace('model_reasoning_effort = "high"',
                                               'model_reasoning_effort = "low"'), encoding="utf-8")
            self.assertTrue(any("Codex Main default must remain High" in failure
                                for failure in verify_materialized.check(root)))
            config.write_text(original, encoding="utf-8")
            for content in (
                'model_reasoning_effort = "high"\nsandbox_mode = "danger-full-access"\napproval_policy = "never"\n',
                'model_reasoning_effort = "high"\nsandbox_mode = "workspace-write"\napproval_policy = "never"\napprovals_reviewer = "user"\n',
                'model_reasoning_effort = "high"\nsandbox_mode = "workspace-write"\napproval_policy = "on-request"\napprovals_reviewer = "auto_review"\n',
            ):
                with self.subTest(content=content):
                    config.write_text(content,encoding="utf-8")
                    self.assertTrue(any("Codex protected manual defaults" in failure
                                        for failure in verify_materialized.check(root)))
            config.write_text('model_reasoning_effort = "high"\n'
                              'sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n'
                              'approvals_reviewer = "user"\n'
                              '[sandbox_workspace_write]\nnetwork_access = false\n'
                              '[shell_environment_policy]\ninherit = "core"\n'
                              'ignore_default_excludes = false\n',encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])
            config.write_bytes(b"\xff")
            self.assertEqual(next(entry for entry in verify_materialized.inspect(root)
                                  if entry["check_id"] == "profile.finalized")["status"],"fail")

    def test_selected_codex_rejects_executable_and_unselected_extensions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            config=root/".codex/config.toml"
            baseline=config.read_text(encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])
            extensions=(
                ("mcp",baseline+'[mcp_servers.synthetic]\ncommand = "synthetic-command"\n'),
                ("hook",baseline+'[hooks.SessionStart]\ncommand = "synthetic-command"\n'),
                ("plugin",baseline+'[plugins.synthetic]\nenabled = true\n'),
                ("notify",'notify = ["synthetic-command"]\n'+baseline),
                ("nested",baseline+'set = {TEST = "synthetic"}\n'),
            )
            for label,content in extensions:
                with self.subTest(extension=label):
                    config.write_text(content,encoding="utf-8")
                    failures=verify_materialized.check(root)
                    self.assertTrue(any("Unselected Codex configuration key" in failure
                                        for failure in failures),failures)
                    with self.assertRaisesRegex(ValueError,"Unselected Codex configuration key"):
                        reject_unselected_codex_config(tomllib.loads(content))
            config.write_text(baseline,encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])

    def test_selected_codex_agent_concurrency_is_typed_and_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            config=root/".codex/config.toml";baseline=config.read_text(encoding="utf-8")
            for value,allowed in (("1",True),("2",True),("0",False),("3",False),
                                  ("1000",False),("true",False),('"2"',False)):
                with self.subTest(value=value):
                    config.write_text(baseline+"\n[agents]\nmax_concurrent_threads_per_session = "+value+"\n",
                                      encoding="utf-8")
                    failures=verify_materialized.check(root)
                    self.assertEqual(not failures,allowed,failures)
                    if not allowed:
                        self.assertTrue(any("agent concurrency" in failure for failure in failures),failures)
            for body,allowed in (("enabled = true\n",False),("enabled = false\n",True),
                                 ('enabled = "true"\nmax_concurrent_threads_per_session = 2\n',False)):
                with self.subTest(agents=body):
                    config.write_text(baseline+"\n[agents]\n"+body,encoding="utf-8")
                    failures=verify_materialized.check(root)
                    self.assertEqual(not failures,allowed,failures)
            config.write_text(baseline,encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])

    def test_codex_template_uses_only_selected_keys(self):
        settings=tomllib.loads((v.ROOT/".codex/config.toml").read_text(encoding="utf-8"))
        reject_unselected_codex_config(settings)

    def test_selected_codex_agents_keep_declared_sandbox_and_keys(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            agents=root/".codex/agents";agents.mkdir()
            for role in ("scout", "worker"):
                shutil.copy2(v.ROOT/".codex/agents"/(role+".toml"),agents/(role+".toml"))
            self.assertEqual(verify_materialized.check(root),[])
            for role,mode in (("scout","read-only"),("worker","workspace-write")):
                path=agents/(role+".toml");original=path.read_text(encoding="utf-8")
                with self.subTest(role=role,change="sandbox"):
                    path.write_text(original.replace('sandbox_mode = "'+mode+'"',
                                                     'sandbox_mode = "danger-full-access"'),encoding="utf-8")
                    self.assertTrue(any("Unsafe Codex agent sandbox" in failure
                                        for failure in verify_materialized.check(root)))
                with self.subTest(role=role,change="mcp"):
                    path.write_text(original+'\n[mcp_servers.synthetic]\ncommand = "synthetic-command"\n',
                                    encoding="utf-8")
                    self.assertTrue(any("Unselected Codex agent configuration key" in failure
                                        for failure in verify_materialized.check(root)))
                with self.subTest(role=role,change="instructions"):
                    path.write_text(original.replace("Do not ", "Please ", 1),encoding="utf-8")
                    self.assertTrue(any("Unreviewed Codex agent instructions" in failure
                                        for failure in verify_materialized.check(root)))
                with self.subTest(role=role,change="description"):
                    path.write_text(original.replace('description = "',
                                                     'description = "Expanded routing for owner decisions: ',1),
                                    encoding="utf-8")
                    self.assertTrue(any("Unreviewed Codex agent description" in failure
                                        for failure in verify_materialized.check(root)))
                with self.subTest(role=role,change="effort"):
                    expected="medium" if role=="scout" else "low"
                    changed="low" if role=="scout" else "medium"
                    path.write_text(original.replace('model_reasoning_effort = "'+expected+'"',
                                                     'model_reasoning_effort = "'+changed+'"'),encoding="utf-8")
                    self.assertTrue(any("Unexpected Codex agent effort" in failure
                                        for failure in verify_materialized.check(root)))
                path.write_text(original,encoding="utf-8")
            extra=agents/"unselected.toml"
            extra.write_text('name = "unselected"\nsandbox_mode = "danger-full-access"\n',encoding="utf-8")
            self.assertTrue(any("Unselected Codex agent configuration" in failure
                                for failure in verify_materialized.check(root)))
            extra.unlink()
            self.assertEqual(verify_materialized.check(root),[])

    def test_selected_claude_agents_keep_reviewed_roles(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            profile["workflow"]["implementation_harnesses"]=["codex","claude_code"]
            path.write_text(json.dumps(profile),encoding="utf-8")
            (root/"CLAUDE.md").write_text("# Claude rules\n",encoding="utf-8")
            native=root/".claude/settings.json";native.parent.mkdir()
            native.write_text(json.dumps({"effortLevel":"high",
                                          "permissions":{"defaultMode":"default",
                                                         "deny":list(v.CLAUDE_CREDENTIAL_DENY_RULES)},
                                          "sandbox":{"enabled":True}}),encoding="utf-8")
            agents=root/".claude/agents";agents.mkdir()
            for role in ("scout","worker"):
                shutil.copy2(v.ROOT/".claude/agents"/(role+".md"),agents/(role+".md"))
            self.assertEqual(verify_materialized.check(root),[])
            for role,effort in (("scout","medium"),("worker","low")):
                agent=agents/(role+".md");original=agent.read_text(encoding="utf-8")
                with self.subTest(role=role,change="effort"):
                    agent.write_text(original.replace("effort: "+effort,"effort: high"),encoding="utf-8")
                    self.assertTrue(any("Unsafe Claude agent role settings" in failure
                                        for failure in verify_materialized.check(root)))
                with self.subTest(role=role,change="instructions"):
                    agent.write_text(original.replace("Do not ","Please ",1),encoding="utf-8")
                    self.assertTrue(any("Unreviewed Claude agent instructions" in failure
                                        for failure in verify_materialized.check(root)))
                if role=="scout":
                    with self.subTest(role=role,change="tools"):
                        agent.write_text(original.replace("tools: Read, Grep, Glob",
                                                          "tools: Read, Grep, Glob, Bash"),encoding="utf-8")
                        self.assertTrue(any("Unsafe Claude agent role settings" in failure
                                            for failure in verify_materialized.check(root)))
                agent.write_text(original,encoding="utf-8")
            extra=agents/"unselected.md"
            extra.write_text("---\nname: unselected\n---\nUnsafe role.\n",encoding="utf-8")
            self.assertTrue(any("Unselected Claude agent configuration" in failure
                                for failure in verify_materialized.check(root)))
            extra.unlink()
            self.assertEqual(verify_materialized.check(root),[])

    def test_v3_selected_codex_rejects_widened_sandbox_network(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            config=root/".codex/config.toml"
            self.assertEqual(verify_materialized.check(root),[])
            protected='model_reasoning_effort = "high"\n' \
                      'sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n' \
                      'approvals_reviewer = "user"\n'
            safe_environment='[shell_environment_policy]\ninherit = "core"\nignore_default_excludes = false\n'
            for network in ('[sandbox_workspace_write]\nnetwork_access = true\n',
                            '[sandbox_workspace_write]\n', ''):
                with self.subTest(network=network):
                    config.write_text(protected+network,encoding="utf-8")
                    self.assertTrue(any("sandbox network must be disabled" in failure
                                        for failure in verify_materialized.check(root)))
            config.write_text(protected+'[sandbox_workspace_write]\nnetwork_access = false\n'+safe_environment,
                              encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])
            config.write_text(protected+'[sandbox_workspace_write]\nnetwork_access = false\n'
                              'writable_roots = ["../outside"]\n'+safe_environment,encoding="utf-8")
            self.assertTrue(any("writable roots must not be widened" in failure
                                for failure in verify_materialized.check(root)))
            config.write_text(protected+'[sandbox_workspace_write]\nnetwork_access = false\n'
                              'writable_roots = []\n'+safe_environment,encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])

    def test_native_config_reader_rejects_links_and_special_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.materialized_fixture(root)
            for relative, executor in ((".codex/config.toml", "Codex"),
                                       (".claude/settings.json", "Claude")):
                with self.subTest(executor=executor):
                    native = root / relative
                    native.parent.mkdir(parents=True, exist_ok=True)
                    native.write_bytes(b"synthetic settings\n")
                    self.assertEqual(verify_materialized.read_native_config(native, executor),
                                     "synthetic settings\n")
                    with native.open("wb") as stream:
                        stream.truncate(verify_materialized.MAX_TEXT_BYTES + 1)
                    with self.assertRaisesRegex(ValueError, "too large"):
                        verify_materialized.read_native_config(native, executor)
                    native.unlink()
                    outside = root / "outside.txt"
                    outside.write_text("synthetic outside\n", encoding="utf-8")
                    try:
                        native.symlink_to(outside)
                    except OSError:
                        pass  # Windows may deny symlink creation without developer mode.
                    else:
                        with self.assertRaisesRegex(ValueError, "regular, unlinked file"):
                            verify_materialized.read_native_config(native, executor)
                        native.unlink()
                    if hasattr(os, "mkfifo"):
                        os.mkfifo(native)
                        with self.assertRaisesRegex(ValueError, "regular, unlinked file"):
                            verify_materialized.read_native_config(native, executor)
                        native.unlink()

    def test_v3_selected_codex_rejects_broad_environment_inheritance(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.materialized_fixture(root)
            config=root/".codex/config.toml"
            protected='model_reasoning_effort = "high"\n' \
                      'sandbox_mode = "workspace-write"\napproval_policy = "on-request"\n' \
                      'approvals_reviewer = "user"\n' \
                      '[sandbox_workspace_write]\nnetwork_access = false\n'
            for environment in ('', '[shell_environment_policy]\ninherit = "all"\n'
                                'ignore_default_excludes = false\n',
                                '[shell_environment_policy]\ninherit = "core"\n'
                                'ignore_default_excludes = true\n'):
                with self.subTest(environment=environment):
                    config.write_text(protected+environment,encoding="utf-8")
                    self.assertTrue(any("environment inheritance is too broad" in failure
                                        for failure in verify_materialized.check(root)))
            config.write_text(protected+'[shell_environment_policy]\ninherit = "core"\n'
                              'ignore_default_excludes = false\n',encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])

    def test_v3_selected_claude_config_requires_protected_manual_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            profile["workflow"]["implementation_harnesses"]=["codex","claude_code"]
            path.write_text(json.dumps(profile),encoding="utf-8")
            (root/"CLAUDE.md").write_text("# Claude rules\n",encoding="utf-8")
            settings=root/".claude/settings.json";settings.parent.mkdir()
            def write_settings(mode,enabled,*,deny=None,effort="high"):
                settings.write_text(json.dumps({"effortLevel":effort,
                                                "permissions":{"defaultMode":mode,
                                                               "deny":list(v.CLAUDE_CREDENTIAL_DENY_RULES)
                                                               if deny is None else deny},
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
            for missing in v.CLAUDE_CREDENTIAL_DENY_RULES:
                with self.subTest(missing=missing):
                    write_settings("default",True,deny=list(v.CLAUDE_CREDENTIAL_DENY_RULES-{missing}))
                    self.assertTrue(any("Claude credential-deny rules are missing" in failure
                                        for failure in verify_materialized.check(root)))
            write_settings("default",True,deny=[])
            self.assertTrue(any("Claude credential-deny rules are missing" in failure
                                for failure in verify_materialized.check(root)))
            write_settings("default",True,deny={rule:True for rule in v.CLAUDE_CREDENTIAL_DENY_RULES})
            self.assertTrue(any("Claude credential-deny rules are missing" in failure
                                for failure in verify_materialized.check(root)))
            write_settings("default",True,effort="low")
            self.assertTrue(any("Claude Main default must remain High" in failure
                                for failure in verify_materialized.check(root)))
            write_settings("default",True)
            self.assertEqual(verify_materialized.check(root),[])

    def test_selected_claude_rejects_executable_and_unselected_settings(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            profile["workflow"]["implementation_harnesses"]=["codex","claude_code"]
            path.write_text(json.dumps(profile),encoding="utf-8")
            (root/"CLAUDE.md").write_text("# Claude rules\n",encoding="utf-8")
            native=root/".claude/settings.json";native.parent.mkdir()
            baseline={"effortLevel":"high",
                      "permissions":{"defaultMode":"default",
                                     "deny":list(v.CLAUDE_CREDENTIAL_DENY_RULES)},
                      "sandbox":{"enabled":True}}
            native.write_text(json.dumps(baseline),encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])
            subprocess.run(["git","init","-q",str(root)],check=True)
            (root/".gitignore").write_text(".claude/settings.local.json\n",encoding="utf-8")
            local=root/".claude/settings.local.json"
            local.write_text(json.dumps({"permissions":{"defaultMode":"bypassPermissions"},
                                         "hooks":{"SessionStart":[{"hooks":[{"type":"command",
                                                                             "command":"synthetic-command"}]}]}}),
                             encoding="utf-8")
            tracked,untracked=v.project_inventory(root)
            self.assertNotIn(local,tracked+untracked)
            self.assertTrue(any("Unselected project-local configuration remains: .claude/settings.local.json"
                                in failure for failure in verify_materialized.check(root)))
            with self.assertRaisesRegex(ValueError,"Unselected project-local configuration remains"):
                v.materialized_profile(profile,root)
            local.unlink()
            mcp=root/".mcp.json"
            mcp.write_text('{"mcpServers":{"synthetic":{"command":"synthetic-command"}}}',encoding="utf-8")
            self.assertTrue(any("Unselected project-local configuration remains: .mcp.json"
                                in failure for failure in verify_materialized.check(root)))
            mcp.unlink()
            self.assertEqual(verify_materialized.check(root),[])
            extensions=(
                ("hook", {"hooks":{"SessionStart":[{"hooks":[{"type":"command",
                                                               "command":"synthetic-command"}]}]}}),
                ("mcp", {"mcpServers":{"synthetic":{"command":"synthetic-command"}}}),
                ("plugin", {"enabledPlugins":{"synthetic":True}}),
                ("nested_permission", {"permissions":{"defaultMode":"default",
                                                        "deny":list(v.CLAUDE_CREDENTIAL_DENY_RULES),
                                                        "additionalDirectories":["../outside"]}}),
                ("nested_sandbox", {"sandbox":{"enabled":True,"excludedCommands":["synthetic"]}}),
            )
            for label,extra in extensions:
                with self.subTest(extension=label):
                    settings={**baseline,**extra}
                    native.write_text(json.dumps(settings),encoding="utf-8")
                    failures=verify_materialized.check(root)
                    self.assertTrue(any("Unselected Claude configuration key" in failure
                                        for failure in failures),failures)
                    with self.assertRaisesRegex(ValueError,"Unselected Claude configuration key"):
                        reject_unselected_claude_config(settings)
            native.write_text(json.dumps(baseline),encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])

    def test_claude_template_uses_only_selected_keys(self):
        settings=v.load_json(v.ROOT/".claude/settings.json")
        reject_unselected_claude_config(settings)

    def test_claude_credential_denials_are_a_string_array_on_both_surfaces(self):
        allowed = list(v.CLAUDE_CREDENTIAL_DENY_RULES)
        self.assertTrue(v.valid_claude_credential_denials(allowed))
        for malformed in (None, {}, {rule:True for rule in allowed}, allowed[:-1], allowed+[1]):
            with self.subTest(malformed=malformed):
                self.assertFalse(v.valid_claude_credential_denials(malformed))

    def test_native_default_gate_is_v3_and_selected_executor_only(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            claude=root/".claude/settings.json";claude.parent.mkdir()
            claude.write_text('{"hooks":{"SessionStart":[{"hooks":[{"type":"command",'
                              '"command":"synthetic-command"}]}]},'
                              '"mcpServers":{"synthetic":{"command":"synthetic-command"}}}',encoding="utf-8")
            self.assertTrue(any("Disabled executor artifact remains: .claude" in failure
                                for failure in verify_materialized.check(root)))
            with self.assertRaisesRegex(ValueError,"Disabled executor artifact remains: .claude"):
                v.materialized_profile(profile,root)
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
            (root/"CLAUDE.md").write_text("# Legacy Claude rules\n",encoding="utf-8")
            claude.write_text('{"permissions":{"defaultMode":"bypassPermissions"},'
                              '"hooks":{"SessionStart":[{"hooks":[{"type":"command",'
                              '"command":"synthetic-command"}]}]}}',encoding="utf-8")
            (root/".codex/config.toml").write_text('sandbox_mode = "danger-full-access"\n'
                                                  'approval_policy = "never"\n'
                                                  '[mcp_servers.legacy]\n'
                                                  'command = "synthetic-command"\n',encoding="utf-8")
            (root/".claude/settings.local.json").write_text('{"hooks":{"SessionStart":[]}}',encoding="utf-8")
            (root/".mcp.json").write_text('{"mcpServers":{"synthetic":{"command":"synthetic-command"}}}',
                                          encoding="utf-8")
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
            for name in verify_materialized.CONSOLE_ASSETS:
                shutil.copy2(v.BOOT/"console"/name,console/name)
            self.assertEqual(verify_materialized.check(root),[])
            (console/"index.html").write_text('<!doctype html><script src="missing.js"></script>')
            self.assertTrue(any("reference missing" in x for x in verify_materialized.check(root)))

    def test_v3_disabled_executor_artifacts_must_be_pruned_in_both_directions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);profile,path=self.materialized_fixture(root)
            self.assertEqual(verify_materialized.check(root),[])
            for relative in ("CLAUDE.md", ".claude/settings.json", ".claude/agents/scout.md",
                             ".mcp.json"):
                with self.subTest(disabled="claude_code", path=relative):
                    extra=root/relative;extra.parent.mkdir(parents=True,exist_ok=True)
                    content=('{"mcpServers":{"synthetic":{"command":"synthetic-command"}}}'
                             if relative == ".mcp.json" else "synthetic unselected artifact\n")
                    extra.write_text(content,encoding="utf-8")
                    self.assertTrue(any("Disabled executor artifact remains" in failure
                                        for failure in verify_materialized.check(root)))
                    extra.unlink()
                    if relative.startswith(".claude/"):
                        for directory in (extra.parent,root/".claude"):
                            if directory.exists():
                                directory.rmdir()
            self.assertEqual(verify_materialized.check(root),[])

            (root/"AGENTS.md").unlink()
            (root/".codex/config.toml").unlink()
            (root/".codex").rmdir()
            profile["workflow"]["implementation_harnesses"]=["claude_code"]
            path.write_text(json.dumps(profile),encoding="utf-8")
            (root/"CLAUDE.md").write_text("# Claude rules\n",encoding="utf-8")
            native=root/".claude/settings.json";native.parent.mkdir()
            native.write_text(json.dumps({"effortLevel":"high",
                                          "permissions":{"defaultMode":"default",
                                                         "deny":list(v.CLAUDE_CREDENTIAL_DENY_RULES)},
                                          "sandbox":{"enabled":True}}),encoding="utf-8")
            self.assertEqual(verify_materialized.check(root),[])
            for relative in ("AGENTS.md", ".codex/config.toml", ".codex/agents/scout.toml"):
                with self.subTest(disabled="codex", path=relative):
                    extra=root/relative;extra.parent.mkdir(parents=True,exist_ok=True)
                    content=('[mcp_servers.synthetic]\ncommand = "synthetic-command"\n'
                             if relative == ".codex/config.toml" else "synthetic unselected artifact\n")
                    extra.write_text(content,encoding="utf-8")
                    self.assertTrue(any("Disabled executor artifact remains" in failure
                                        for failure in verify_materialized.check(root)))
                    extra.unlink()
                    if relative.startswith(".codex/"):
                        for directory in (extra.parent,root/".codex"):
                            if directory.exists():
                                directory.rmdir()
            self.assertEqual(verify_materialized.check(root),[])

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
