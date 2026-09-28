"""Disposable Git repositories only; never touch the owner's actual project."""
from __future__ import annotations
import importlib.util
import os
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
    def directory_link(self, link, target):
        try:
            link.symlink_to(target,target_is_directory=True)
        except OSError:
            if os.name!='nt': raise
            subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(link),str(target)],check=True,capture_output=True)

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
            self.directory_link(home/'points_to_original',original)
            with self.assertRaisesRegex(ValueError,'not be nested'):
                adoption.prepare(original,home/'points_to_original'/'sandbox')
            adoption.prepare(original,sandbox)
            outside=home/'outside';outside.mkdir();(outside/'escape.txt').write_text('outside\n')
            self.directory_link(sandbox/'linked',outside)
            command(sandbox,'add','linked')
            command(sandbox,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','symlink')
            with self.assertRaisesRegex(ValueError,'Unsafe symlink'):
                adoption.inspect(sandbox)

    def test_complete_adoption_preserves_three_existing_product_shapes(self):
        for kind in ("static", "native_cli", "game_mod"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                home=Path(directory);original=self.fixture(home);sandbox=home/"sandbox"
                (original/"AGENTS.md").write_text("# Old method\nDo not use Issues.\n",encoding="utf-8")
                (original/"KNOWLEDGE.md").write_text("Useful product behavior.\n",encoding="utf-8")
                (original/"project.json").write_text('{"kind":"'+kind+'","optional_resource":"missing.asset"}\n',encoding="utf-8")
                (original/".gitignore").write_text(".local/\n",encoding="utf-8")
                if kind == "native_cli":
                    (original/"tool.py").write_text("print('native check passed')\n",encoding="utf-8")
                if kind == "game_mod":
                    (original/"loader-script.txt").write_text("useful synthetic loader instructions\n",encoding="utf-8")
                local=original/".local/config.json";local.parent.mkdir(parents=True);local.write_text('{"machine":"synthetic"}\n',encoding="utf-8")
                command(original,"add",".");command(original,"commit","-qm","existing product knowledge and tools")
                baseline=adoption.sha(original)
                adoption.prepare(original,sandbox)
                (sandbox/"AGENTS.md").write_text("# Current method\nGitHub Issues own active work.\n",encoding="utf-8")
                command(sandbox,"add","AGENTS.md")
                command(sandbox,"-c","user.name=Fixture","-c","user.email=fixture@example.invalid","commit","-qm","adopt current method")
                report=adoption.inspect(sandbox)
                self.assertEqual(report["changed"],[("M","AGENTS.md")])
                adoption.apply(sandbox,report["approved_head_candidate"])
                self.assertEqual(adoption.sha(original),baseline)
                self.assertIn("Issues own active work",(original/"AGENTS.md").read_text(encoding="utf-8"))
                self.assertEqual((original/"KNOWLEDGE.md").read_text(encoding="utf-8"),"Useful product behavior.\n")
                self.assertFalse((original/"missing.asset").exists())
                self.assertEqual(local.read_text(encoding="utf-8"),'{"machine":"synthetic"}\n')
                if kind == "native_cli":
                    result=subprocess.run(["python",str(original/"tool.py")],check=True,capture_output=True,text=True)
                    self.assertEqual(result.stdout.strip(),"native check passed")
                if kind == "game_mod":
                    self.assertEqual((original/"loader-script.txt").read_text(encoding="utf-8"),"useful synthetic loader instructions\n")


if __name__=="__main__":unittest.main()
