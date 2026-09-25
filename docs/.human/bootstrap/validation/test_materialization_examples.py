"""Small disposable outputs: structural gate plus a native product check."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import validate as v

spec=importlib.util.spec_from_file_location('postcheck',v.HERE/'verify-materialized.py')
postcheck=importlib.util.module_from_spec(spec);spec.loader.exec_module(postcheck)


class MaterializationExamples(unittest.TestCase):
    def make(self,root,kind):
        (root/'docs/.ai').mkdir(parents=True)
        for name,body in [('PROJECT_GUIDE.md','# Project guide\n'),('README.md','# Product\n'),
                          ('AGENTS.md','# Codex task rules\n'),('VERSION','1.0\n'),
                          ('docs/.ai/SECURITY_BASELINE.md','# Selected local controls\n')]:
            (root/name).write_text(body)
        profile=v.load_json(v.ROOT/'docs/.ai/project-profile.json')
        profile['project']={'name':'Synthetic '+kind,'kind':kind,'summary':'Disposable check'}
        profile['versioning'].update(canonical_source='VERSION',format='native')
        profile['security'].update(exposure='local',control_map='docs/.ai/SECURITY_BASELINE.md')
        profile['workflow']['implementation_harnesses']=['codex']
        (root/'docs/.ai/project-profile.json').write_text(json.dumps(profile))

    def test_static_site_without_services_or_build(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.make(root,'static')
            (root/'index.html').write_text('<!doctype html><title>Example</title><p>Hello</p>')
            self.assertEqual(postcheck.check(root),[])
            self.assertIn('<p>Hello</p>',(root/'index.html').read_text())
            self.assertEqual(v.load_json(root/'docs/.ai/project-profile.json')['distribution']['mode'],'none')
            self.assertFalse((root/'project-console').exists())

    def test_local_cli_native_behavior_and_pruning(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.make(root,'cli')
            (root/'tool.py').write_text('import sys\nprint("Hello, " + sys.argv[1])\n')
            output=subprocess.run(['python',str(root/'tool.py'),'Example'],capture_output=True,text=True,check=True)
            self.assertEqual(output.stdout.strip(),'Hello, Example')
            self.assertEqual(postcheck.check(root),[])
            (root/'docs/.human/bootstrap').mkdir(parents=True)
            self.assertIn('bootstrap directory remains',postcheck.check(root))


if __name__=='__main__':unittest.main()
