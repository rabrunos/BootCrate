import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('managed',Path(__file__).resolve().parents[1]/'upgrade/managed.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class UpgradeTests(unittest.TestCase):
    def setup_roots(self,home):
        root=home/'project';source=home/'new';root.mkdir();source.mkdir()
        (root/'docs/.human/bootstrap').mkdir(parents=True)
        for name,content in [('update.txt','base'),('custom.txt','base'),('retire.txt','base'),('missing.txt','base')]:
            (root/name).write_text(content)
        return root,source

    def test_three_way_rules_and_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            root,source=self.setup_roots(Path(td))
            m.create(root,'rev1',['update.txt','custom.txt','retire.txt'])
            (source/'update.txt').write_text('new')
            (source/'custom.txt').write_text('base')
            (root/'custom.txt').write_text('owner customization')
            (source/'added.txt').write_text('new file')
            plan=m.preview(root,source,m.read(root),['added.txt'])
            actions={x['path']:x['action'] for x in plan['actions']}
            self.assertEqual(actions,{'added.txt':'add','custom.txt':'preserve','retire.txt':'remove','update.txt':'update'})
            self.assertEqual((root/'update.txt').read_text(),'base')
            m.apply(root,source,plan['digest'],'rev2',['added.txt'])
            self.assertEqual((root/'update.txt').read_text(),'new')
            self.assertEqual((root/'custom.txt').read_text(),'owner customization')
            self.assertFalse((root/'retire.txt').exists())
            self.assertEqual((root/'added.txt').read_text(),'new file')
            with self.assertRaisesRegex(ValueError,'Plan or file contents changed'):
                m.apply(root,source,plan['digest'],'rev2',['added.txt'])

    def test_conflicts_and_rechecks_block(self):
        with tempfile.TemporaryDirectory() as td:
            root,source=self.setup_roots(Path(td))
            m.create(root,'rev1',['update.txt','missing.txt'])
            (source/'update.txt').write_text('new')
            (root/'update.txt').write_text('owner edit')
            (root/'missing.txt').unlink()
            conflicts=m.preview(root,source,m.read(root))
            self.assertTrue(all(x['action']=='conflict' for x in conflicts['actions']))
            with self.assertRaisesRegex(ValueError,'conflicts'):
                m.apply(root,source,conflicts['digest'],'rev2')
            (root/'update.txt').write_text('base')
            planned=m.preview(root,source,m.read(root))
            (source/'update.txt').write_text('changed since preview')
            with self.assertRaisesRegex(ValueError,'changed since review'):
                m.apply(root,source,planned['digest'],'rev2')

    def test_new_path_collision_escape_and_pruned_block(self):
        with tempfile.TemporaryDirectory() as td:
            root,source=self.setup_roots(Path(td));m.create(root,'rev1',['update.txt'])
            (root/'foreign.txt').write_text('belongs to project');(source/'foreign.txt').write_text('template')
            self.assertEqual(m.preview(root,source,m.read(root),['foreign.txt'])['actions'][0]['action'],'conflict')
            with self.assertRaisesRegex(ValueError,'Unsafe managed path'):m.resolve(root,'../outside')
            (root/'docs/.human/bootstrap').rmdir()
            with self.assertRaisesRegex(ValueError,'pruned'):m.read(root)


if __name__=='__main__':unittest.main()
