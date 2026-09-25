"""Disposable Git repositories only; never touch the owner's actual project."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("adoption", HERE.parent/"adoption/adoption.py")
adoption=importlib.util.module_from_spec(spec);spec.loader.exec_module(adoption)


def command(root,*args):
    return subprocess.run(["git",*args],cwd=root,check=True,capture_output=True)


class AdoptionTests(unittest.TestCase):
    def fixture(self, home):
        original=home/"original";original.mkdir();command(original,"init","-q")
        command(original,"config","user.name","Fixture")
        command(original,"config","user.email","fixture@example.invalid")
        (original/"product.txt").write_text("working product\n")
        command(original,"add",".");command(original,"commit","-qm","baseline")
        return original

    def test_sandbox_isolated_and_reviewed_delta_only(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);original=self.fixture(home);sandbox=home/"sandbox"
            adoption.prepare(original,sandbox)
            self.assertEqual((original/"product.txt").read_text(),"working product\n")
            self.assertFalse(command(sandbox,"remote").stdout.strip())
            (sandbox/"product.txt").write_text("working product with adopted method\n")
            (sandbox/"guide.md").write_text("selected new instructions\n")
            command(sandbox,"-c","user.name=Fixture","-c","user.email=fixture@example.invalid","add",".")
            command(sandbox,"-c","user.name=Fixture","-c","user.email=fixture@example.invalid","commit","-qm","adopt")
            report=adoption.inspect(sandbox)
            self.assertEqual({x[1] for x in report["changed"]},{"product.txt","guide.md"})
            self.assertEqual((original/"product.txt").read_text(),"working product\n")
            self.assertEqual(adoption.apply(sandbox,report["approved_head_candidate"])["status"],"applied_uncommitted")
            self.assertEqual((original/"product.txt").read_text(),"working product with adopted method\n")
            with self.assertRaisesRegex(ValueError,"baseline changed"):
                adoption.apply(sandbox,report["approved_head_candidate"])

    def test_drift_or_wrong_head_blocks_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);original=self.fixture(home);sandbox=home/"sandbox"
            adoption.prepare(original,sandbox)
            (sandbox/"guide.md").write_text("adopted\n")
            command(sandbox,"add",".")
            command(sandbox,"-c","user.name=Fixture","-c","user.email=fixture@example.invalid","commit","-qm","adopt")
            with self.assertRaisesRegex(ValueError,"after review"):
                adoption.apply(sandbox,"deadbeef")
            (original/"product.txt").write_text("owner change\n")
            with self.assertRaisesRegex(ValueError,"baseline changed"):
                adoption.apply(sandbox,adoption.sha(sandbox))

    def test_local_changes_are_explicitly_included_in_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);original=self.fixture(home);sandbox=home/"sandbox"
            (original/"product.txt").write_text("owner uncommitted work\n")
            (original/"untracked.txt").write_text("owner local file\n")
            with self.assertRaisesRegex(ValueError,"include-local-changes"):
                adoption.prepare(original,sandbox)
            adoption.prepare(original,sandbox,include_local_changes=True)
            self.assertEqual((sandbox/"product.txt").read_text(),"owner uncommitted work\n")
            self.assertEqual((sandbox/"untracked.txt").read_text(),"owner local file\n")
            self.assertEqual(adoption.inspect(sandbox)["changed"],[])

    def test_symlinked_destination_and_committed_symlink_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);original=self.fixture(home);sandbox=home/'sandbox'
            (home/'points_to_original').symlink_to(original,target_is_directory=True)
            with self.assertRaisesRegex(ValueError,'not be nested'):
                adoption.prepare(original,home/'points_to_original'/'sandbox')
            adoption.prepare(original,sandbox)
            (sandbox/'linked').symlink_to('/tmp/outside')
            command(sandbox,'add','linked')
            command(sandbox,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','symlink')
            with self.assertRaisesRegex(ValueError,'Unsafe symlink'):
                adoption.inspect(sandbox)


if __name__=="__main__":unittest.main()
