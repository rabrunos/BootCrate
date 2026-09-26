import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('managed',Path(__file__).resolve().parents[1]/'upgrade/managed.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class UpgradeTests(unittest.TestCase):
    def setup_roots(self,home):
        root=home/'project';source=home/'new';root.mkdir();source.mkdir()
        (root/'docs/.human/bootstrap').mkdir(parents=True)
        for name,content in [('update.txt','base'),('custom.txt','base'),('retire.txt','base'),('missing.txt','base')]:
            (root/name).write_text(content)
        return root,source

    def two_file_upgrade(self, home):
        root,source=self.setup_roots(home)
        for name in ('a.txt','b.txt'):
            (root/name).write_text('original-'+name)
            (source/name).write_text('approved-'+name)
        m.create(root,'rev1',['a.txt','b.txt'])
        return root,source,m.preview(root,source,m.read(root))

    def directory_link(self, link, target):
        try:
            link.symlink_to(target,target_is_directory=True)
        except OSError:
            if os.name!='nt':
                raise
            subprocess.run(
                ['cmd.exe','/d','/c','mklink','/J',str(link),str(target)],
                check=True,capture_output=True,
            )

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

    def test_destination_change_between_files_is_preserved_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as td:
            root,source,plan=self.two_file_upgrade(Path(td))
            original_replace=m._replace_file
            def interleave(staged,target):
                original_replace(staged,target)
                if target==root/'a.txt':
                    (root/'b.txt').write_text('owner concurrent edit')
            with patch.object(m,'_replace_file',side_effect=interleave):
                with self.assertRaisesRegex(ValueError,'changed before write'):
                    m.apply(root,source,plan['digest'],'rev2')
            self.assertEqual((root/'a.txt').read_text(),'original-a.txt')
            self.assertEqual((root/'b.txt').read_text(),'owner concurrent edit')
            self.assertEqual(m.read(root)['source_revision'],'rev1')

    def test_source_bytes_are_frozen_before_first_write(self):
        with tempfile.TemporaryDirectory() as td:
            root,source,plan=self.two_file_upgrade(Path(td))
            original_replace=m._replace_file
            def interleave(staged,target):
                original_replace(staged,target)
                if target==root/'a.txt':
                    (source/'b.txt').write_text('unapproved later source')
            with patch.object(m,'_replace_file',side_effect=interleave):
                m.apply(root,source,plan['digest'],'rev2')
            self.assertEqual((root/'b.txt').read_text(),'approved-b.txt')
            self.assertEqual(
                m.read(root)['files']['b.txt'],m.hash_bytes((root/'b.txt').read_bytes())
            )

    def test_manifest_change_and_second_write_failure_restore_only_own_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root,source,plan=self.two_file_upgrade(Path(td))
            original_replace=m._replace_file
            def change_manifest(staged,target):
                original_replace(staged,target)
                if target==root/'a.txt':
                    manifest=root/m.MANIFEST
                    manifest.write_bytes(manifest.read_bytes()+b'\n')
            with patch.object(m,'_replace_file',side_effect=change_manifest):
                with self.assertRaisesRegex(ValueError,'Manifest changed'):
                    m.apply(root,source,plan['digest'],'rev2')
            self.assertEqual((root/'a.txt').read_text(),'original-a.txt')
            self.assertEqual((root/'b.txt').read_text(),'original-b.txt')
            self.assertTrue((root/m.MANIFEST).read_bytes().endswith(b'\n\n'))

        with tempfile.TemporaryDirectory() as td:
            root,source,plan=self.two_file_upgrade(Path(td))
            original_replace=m._replace_file
            def fail_second(staged,target):
                if target==root/'b.txt':
                    raise OSError('synthetic second write failure')
                original_replace(staged,target)
            with patch.object(m,'_replace_file',side_effect=fail_second):
                with self.assertRaisesRegex(OSError,'second write failure'):
                    m.apply(root,source,plan['digest'],'rev2')
            self.assertEqual((root/'a.txt').read_text(),'original-a.txt')
            self.assertEqual((root/'b.txt').read_text(),'original-b.txt')
            self.assertEqual(m.read(root)['source_revision'],'rev1')

    def test_manifest_commit_failure_and_concurrent_rollback_edit(self):
        with tempfile.TemporaryDirectory() as td:
            root,source,plan=self.two_file_upgrade(Path(td))
            original_replace=m._replace_file
            def fail_manifest(staged,target):
                if target==root/m.MANIFEST and staged.name=='manifest-after':
                    raise OSError('synthetic manifest commit failure')
                original_replace(staged,target)
            with patch.object(m,'_replace_file',side_effect=fail_manifest):
                with self.assertRaisesRegex(OSError,'manifest commit failure'):
                    m.apply(root,source,plan['digest'],'rev2')
            self.assertEqual((root/'a.txt').read_text(),'original-a.txt')
            self.assertEqual((root/'b.txt').read_text(),'original-b.txt')
            self.assertEqual(m.read(root)['source_revision'],'rev1')

        with tempfile.TemporaryDirectory() as td:
            root,source,plan=self.two_file_upgrade(Path(td))
            original_replace=m._replace_file
            def edit_during_failure(staged,target):
                if target==root/'b.txt':
                    (root/'a.txt').write_text('owner edit during recovery')
                    raise OSError('synthetic failure after owner edit')
                original_replace(staged,target)
            with patch.object(m,'_replace_file',side_effect=edit_during_failure):
                with self.assertRaisesRegex(RuntimeError,'Recovery incomplete'):
                    m.apply(root,source,plan['digest'],'rev2')
            self.assertEqual((root/'a.txt').read_text(),'owner edit during recovery')
            self.assertEqual((root/'b.txt').read_text(),'original-b.txt')
            recoveries=list((root/'.local').glob('bootcrate-upgrade-txn-*/recovery.json'))
            self.assertEqual(len(recoveries),1)
            self.assertIn('recovery_incomplete',recoveries[0].read_text())

    def test_control_directory_link_cannot_escape_project(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td);root,source=self.setup_roots(home);outside=home/'outside';outside.mkdir()
            self.directory_link(root/'.local',outside)
            link = root/'.local'
            try:
                with self.assertRaisesRegex(ValueError,'reparse point|Unsafe'):
                    m.create(root,'rev1',['update.txt'])
                self.assertFalse((outside/'bootcrate-managed.json').exists())
                self.assertEqual((root/'update.txt').read_text(),'base')
            finally:
                if link.is_symlink(): link.unlink()
                else: os.rmdir(link)  # Windows junction fallback.

    def test_repeat_is_idempotent_and_customization_stays_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root,source=self.setup_roots(Path(td))
            m.create(root,'rev1',['update.txt','custom.txt'])
            (source/'update.txt').write_text('new')
            (source/'custom.txt').write_text('base')
            (root/'custom.txt').write_text('owner customization')
            first=m.preview(root,source,m.read(root));m.apply(root,source,first['digest'],'rev2')
            second=m.preview(root,source,m.read(root));result=m.apply(root,source,second['digest'],'rev2')
            self.assertEqual(result['paths'],[])
            self.assertEqual((root/'update.txt').read_text(),'new')
            self.assertEqual((root/'custom.txt').read_text(),'owner customization')


if __name__=='__main__':unittest.main()
