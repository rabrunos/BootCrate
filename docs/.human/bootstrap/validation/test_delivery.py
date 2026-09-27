import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('delivery',Path(__file__).resolve().parents[1]/'delivery/delivery.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
coord_spec=importlib.util.spec_from_file_location('coordination',Path(__file__).resolve().parents[1]/'delivery/coordination.py')
coord=importlib.util.module_from_spec(coord_spec);coord_spec.loader.exec_module(coord)
SOURCE='''# Changelog

## v1.3 — Search

<!-- change:#42/1 audience:public -->
- Corrigidos filtros ao reabrir a busca.

## v1.2 — Export

<!-- change:#41/1 audience:public -->
- Adicionada exportação dos resultados em CSV.

## v1.1 — Internal

<!-- change:#40/1 audience:maintainers -->
- Melhorada a validação de configurações inválidas.
'''


def candidate():
    return {'version':'1.3','source_commit':'a'*40,'payload_sha256':'b'*64,
            'artifacts':{'github':'c'*64,'nexus':'d'*64},
            'included_changes':['#40/1','#41/1','#42/1'],'integration_order':3}


def target(id='github',field='markdown',baseline='never_published'):
    return {'id':id,'channel':'stable','field':field,'baseline':baseline,'max_bytes':5000}


def receipt(version,order,changes,id='github',status='confirmed',attempt=None,observed_at='2026-09-24T00:00:00Z'):
    return {'schema':'bootcrate-receipt/v1','destination':id,'channel':'stable','version':version,
            'integration_order':order,'included_changes':changes,'status':status,
            'attempt_id':attempt or 'attempt-'+id+'-'+version,
            'candidate_id':'f'*64,'artifact_sha256':'e'*64,'evidence_ref':'https://example.invalid/release',
            'observed_by':'authorized operator','observed_at':observed_at}


class DeliveryTests(unittest.TestCase):
    def setUp(self):self.entries=d.changelog(SOURCE)

    def test_bootcrate_itself_keeps_integrated_version_history(self):
        source=Path(__file__).resolve().parents[4]/'CHANGELOG.md'
        versions=[entry['version'] for entry in d.changelog(source.read_text(encoding='utf-8'))]
        self.assertEqual(versions,['0.9','0.8','0.7','0.6','0.5','0.4'])

    def test_work_target_assignment_uses_issue_history_and_fresh_remote_head(self):
        head='a'*40
        records=[{'issue':'#42','target':'1.3.0-alpha.1','status':'assigned'},
                 {'issue':'#41','target':'1.2.0','status':'abandoned'}]
        self.assertEqual(coord.assignment(records,'#42','1.3.0-alpha.1',head,head)['operation'],'continue')
        self.assertEqual(coord.assignment(records,'#43','1.3.0-alpha.1',head,head)['status'],'BLOCK')
        self.assertEqual(coord.assignment(records,'#43','1.2.0',head,head)['status'],'BLOCK')
        self.assertEqual(coord.assignment(records,'#42','1.3.0-alpha.2',head,head)['status'],'BLOCK')
        self.assertEqual(coord.assignment(records,'#43','1.3.0-alpha.2',head,'b'*40)['status'],'BLOCK')
        self.assertEqual(coord.assignment(records,'#43','1.3.0-alpha.2',head,head)['operation'],'propose')
        self.assertEqual(coord.assignment([*records,{'issue':'#43','target':'1.3.0-alpha.1','status':'assigned'}],
                                          '#44','1.4',head,head)['status'],'BLOCK')

    def test_two_contributions_recheck_shared_head_before_serial_integration(self):
        def git(root,*args):
            return subprocess.run(["git",*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);git(root,"init","-q");git(root,"config","user.name","Fixture");git(root,"config","user.email","fixture@example.invalid")
            (root/"base.txt").write_text("baseline\n",encoding="utf-8");git(root,"add",".");git(root,"commit","-qm","baseline")
            base=git(root,"rev-parse","HEAD");main=git(root,"branch","--show-current")
            for branch,name in (("issue-42","search.txt"),("issue-43","export.txt")):
                git(root,"checkout","-qb",branch,base);(root/name).write_text(branch+"\n",encoding="utf-8");git(root,"add",name);git(root,"commit","-qm",branch)
            git(root,"checkout","-q",main)
            self.assertEqual(coord.assignment([],"#42","1.1-alpha.1",base,base)["operation"],"propose")
            self.assertEqual(coord.assignment([],"#43","1.1-alpha.2",base,base)["operation"],"propose")
            git(root,"merge","--no-ff","-qm","integrate #42","issue-42");after_first=git(root,"rev-parse","HEAD")
            self.assertEqual(coord.assignment([],"#43","1.1-alpha.2",base,after_first)["status"],"BLOCK")
            self.assertEqual(coord.assignment([],"#43","1.1-alpha.2",after_first,after_first)["operation"],"propose")
            git(root,"merge","--no-ff","-qm","integrate #43","issue-43")
            self.assertEqual((root/"search.txt").read_text(encoding="utf-8"),"issue-42\n")
            self.assertEqual((root/"export.txt").read_text(encoding="utf-8"),"issue-43\n")

    def test_baseline_independent_and_internal_note_filtered(self):
        old=receipt('1.1',1,['#40/1']);ahead=receipt('1.2',2,['#40/1','#41/1'],id='nexus')
        github=d.plan(candidate(),[old,ahead],target('github',baseline='unknown'),self.entries)
        nexus=d.plan(candidate(),[old,ahead],target('nexus',baseline='unknown'),self.entries)
        self.assertEqual(github['included_changes'],candidate()['included_changes'])
        self.assertEqual(nexus['included_changes'],candidate()['included_changes'])
        self.assertEqual(github['new_change_ids'],['#41/1','#42/1'])
        self.assertEqual(nexus['new_change_ids'],['#42/1'])
        self.assertIn('CSV',github['notes']);self.assertNotIn('configurações',github['notes'])
        self.assertNotIn('CSV',nexus['notes'])

    def test_confirmed_integration_history_must_be_cumulative(self):
        first=receipt('1.1',1,['#40/1'])
        dropped=receipt('1.2',2,['#41/1'])
        result=d.plan(candidate(),[first,dropped],target(baseline='unknown'),self.entries)
        self.assertEqual(result['status'],'BLOCK')
        self.assertIn('not cumulative',result['reason'])

        cumulative=receipt('1.2',2,['#40/1','#41/1'])
        ready=d.plan(candidate(),[first,cumulative],target(baseline='unknown'),self.entries)
        self.assertEqual(ready['status'],'READY')
        self.assertEqual(ready['included_changes'],candidate()['included_changes'])
        self.assertEqual(ready['new_change_ids'],['#42/1'])

        recorded=receipt('1.3',3,ready['included_changes'],attempt='new-attempt')
        recorded.update(candidate_id=ready['candidate_id'],
                        artifact_sha256=ready['artifact_sha256'])
        self.assertEqual(d.plan(candidate(),[first,cumulative,recorded],
                                target(baseline='unknown'),self.entries)['status'],'SKIP')

        conflict=receipt('1.2-alt',2,['#40/1','#41/1'],attempt='other-attempt')
        ambiguous=d.plan(candidate(),[first,cumulative,conflict],target(baseline='unknown'),self.entries)
        self.assertEqual(ambiguous['status'],'BLOCK')
        self.assertIn('Ambiguous confirmed integration order',ambiguous['reason'])

        independent=receipt('1.2',2,['#41/1'],id='nexus')
        self.assertEqual(d.plan(candidate(),[first,independent],target('github',baseline='unknown'),self.entries)['status'],'READY')

    def test_unknown_partial_and_duplicate_behaviors(self):
        self.assertEqual(d.plan(candidate(),[],target(baseline='unknown'),self.entries)['status'],'BLOCK')
        self.assertEqual(d.plan(candidate(),[receipt('1.2',2,['#40/1','#41/1'],status='unknown')],target(),self.entries)['status'],'BLOCK')
        same=receipt('1.3',3,candidate()['included_changes']);same['candidate_id']=d.identity(candidate());same['artifact_sha256']='c'*64
        self.assertEqual(d.plan(candidate(),[same],target(),self.entries)['status'],'SKIP')
        same['artifact_sha256']='d'*64
        self.assertEqual(d.plan(candidate(),[same],target(),self.entries)['status'],'BLOCK')
        unresolved=receipt('1.3',3,candidate()['included_changes'],status='unknown')
        unresolved.update(candidate_id=d.identity(candidate()),artifact_sha256='c'*64)
        resolved={**unresolved,'status':'confirmed','observed_at':'2026-09-24T00:01:00Z'}
        self.assertEqual(d.plan(candidate(),[unresolved,resolved],target(),self.entries)['status'],'SKIP')
        later=receipt('1.4',4,candidate()['included_changes'])
        self.assertEqual(d.plan(candidate(),[resolved,later],target(),self.entries)['status'],'BLOCK')

    def test_boolean_integration_order_cannot_be_a_confirmed_baseline(self):
        current=candidate()
        for malformed in (True,False,1.0,"1"):
            with self.subTest(order=malformed):
                bad=receipt('1.1',malformed,['#40/1'])
                self.assertEqual(d.plan(current,[bad],target(),self.entries)['status'],'BLOCK')
                with self.assertRaisesRegex(ValueError,"Candidate integration order"):
                    d.identity({**current,"integration_order":malformed})
        valid=receipt('1.1',1,['#40/1'])
        self.assertEqual(d.plan(current,[valid],target(),self.entries)['status'],'READY')

    def test_receipt_event_reduction_preserves_confirmation_and_identity(self):
        c=candidate();cid=d.identity(c)
        pending=receipt('1.3',3,c['included_changes'],status='unknown',attempt='same',observed_at='2026-09-24T00:00:00Z')
        pending.update(candidate_id=cid,artifact_sha256='c'*64)
        confirmed={**pending,'status':'confirmed','observed_at':'2026-09-24T00:01:00Z'}
        self.assertEqual(d.plan(c,[confirmed,pending,confirmed],target(),self.entries)['status'],'SKIP')
        failed={**confirmed,'status':'failed','observed_at':'2026-09-24T00:02:00Z'}
        self.assertEqual(d.plan(c,[pending,confirmed,failed],target(),self.entries)['status'],'BLOCK')
        changed={**pending,'version':'1.2'}
        self.assertEqual(d.plan(c,[pending,changed],target(),self.entries)['status'],'BLOCK')
        reused={**pending,'destination':'nexus'}
        self.assertEqual(d.plan(c,[pending,reused],target(),self.entries)['status'],'BLOCK')

    def test_preflight_effects_do_not_duplicate_confirmed_destination(self):
        calls=[]
        def simulated_publisher(preflight):
            if preflight['status']=='READY':calls.append((preflight['destination'],preflight['candidate_id']))
        ready=d.plan(candidate(),[],target(),self.entries);simulated_publisher(ready)
        same=receipt('1.3',3,candidate()['included_changes']);same.update(
            candidate_id=d.identity(candidate()),artifact_sha256='c'*64)
        skipped=d.plan(candidate(),[same],target(),self.entries);simulated_publisher(skipped)
        self.assertEqual(len(calls),1)
        self.assertEqual(skipped['status'],'SKIP')

    def test_confirmed_skip_still_requires_canonical_change_history(self):
        current=candidate()
        same=receipt('1.3',3,current['included_changes'])
        same.update(candidate_id=d.identity(current),artifact_sha256=current['artifacts']['github'])
        self.assertEqual(d.plan(current,[same],target(),self.entries)['status'],'SKIP')

        missing_version=d.plan(current,[same],target(),self.entries[1:])
        self.assertEqual(missing_version['status'],'BLOCK')
        self.assertIn('no canonical changelog entry',missing_version['reason'])

        missing_change=[{**self.entries[0]},*self.entries[1:]]
        missing_change[1]={**missing_change[1],
                           'changes':[change for change in missing_change[1]['changes']
                                      if change['id']!='#41/1']}
        absent=d.plan(current,[same],target(),missing_change)
        self.assertEqual(absent['status'],'BLOCK')
        self.assertIn('missing changelog change',absent['reason'])

        incomplete=candidate();incomplete['included_changes'].remove('#42/1')
        incomplete_same=receipt('1.3',3,incomplete['included_changes'])
        incomplete_same.update(candidate_id=d.identity(incomplete),
                               artifact_sha256=incomplete['artifacts']['github'])
        omitted=d.plan(incomplete,[incomplete_same],target(),self.entries)
        self.assertEqual(omitted['status'],'BLOCK')
        self.assertIn('formalized version entry',omitted['reason'])

    def test_confirmed_skip_requires_matching_receipt_baseline(self):
        current=candidate()
        matching=receipt(current['version'],current['integration_order'],list(current['included_changes']))
        matching.update(candidate_id=d.identity(current),artifact_sha256=current['artifacts']['github'])
        self.assertEqual(d.plan(current,[matching],target(),self.entries)['status'],'SKIP')
        for field,value in (
            ('integration_order',current['integration_order']-1),
            ('integration_order',current['integration_order']+1),
            ('included_changes',current['included_changes'][:-1]),
            ('included_changes',list(reversed(current['included_changes']))),
        ):
            with self.subTest(field=field,value=value):
                inconsistent={**matching,'attempt_id':'other-attempt',field:value}
                blocked=d.plan(current,[inconsistent],target(),self.entries)
                self.assertEqual(blocked['status'],'BLOCK')
                self.assertIn('inconsistent integration metadata',blocked['reason'])
                mixed=d.plan(current,[matching,inconsistent],target(),self.entries)
                self.assertEqual(mixed['status'],'BLOCK')
                self.assertTrue('inconsistent integration metadata' in mixed['reason'] or
                                'Ambiguous confirmed integration order' in mixed['reason'])

    def test_candidate_change_list_is_typed_before_ready(self):
        entries=[{'version':'1.3','title':'Two changes','changes':[
            {'id':'a','text':'First change','audience':'public'},
            {'id':'b','text':'Second change','audience':'public'}]}]
        current=candidate()
        for invalid in ('ab', {'a':'b'}, None, ['a',1], ['a',['b']]):
            with self.subTest(invalid=invalid):
                malformed={**current,'included_changes':invalid}
                with self.assertRaisesRegex(ValueError,'Candidate change identity list is invalid'):
                    d.identity(malformed)
                with self.assertRaisesRegex(ValueError,'Candidate change identity list is invalid'):
                    d.plan(malformed,[],target(),entries)
        current['included_changes']=['a','b']
        ready=d.plan(current,[],target(),entries)
        self.assertEqual(ready['status'],'READY')
        confirmed=receipt('1.3',3,ready['included_changes'])
        confirmed.update(candidate_id=ready['candidate_id'],
                         artifact_sha256=ready['artifact_sha256'])
        self.assertEqual(d.plan(current,[confirmed],target(),entries)['status'],'SKIP')

    def test_artifacts_must_be_a_mapping_before_cli_planning(self):
        for invalid in ([], None, "github", {"github": 1}, {}):
            with self.subTest(artifacts=invalid), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                malformed={**candidate(),"artifacts":invalid}
                with self.assertRaisesRegex(ValueError,"artifacts mapping|artifact digest"):
                    d.identity(malformed)
                paths={name:root/name for name in ("candidate.json","receipts.json",
                                                 "target.json","CHANGELOG.md")}
                paths["candidate.json"].write_text(json.dumps(malformed),encoding="utf-8")
                paths["receipts.json"].write_text("[]",encoding="utf-8")
                paths["target.json"].write_text(json.dumps(target()),encoding="utf-8")
                paths["CHANGELOG.md"].write_text(SOURCE,encoding="utf-8")
                result=subprocess.run([sys.executable,str(Path(d.__file__)),
                                       "--candidate",str(paths["candidate.json"]),
                                       "--receipts",str(paths["receipts.json"]),
                                       "--target",str(paths["target.json"]),
                                       "--changelog",str(paths["CHANGELOG.md"])],
                                      capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,2)
                self.assertIn("BLOCKED:",result.stderr)
                self.assertNotIn("Traceback",result.stderr)

    def test_formats_escapes_and_notes_limit(self):
        first=d.plan(candidate(),[],target(field='plain'),self.entries)
        self.assertIn('CSV',first['notes']);self.assertEqual(first['status'],'READY')
        small=target();small['max_bytes']=5
        self.assertEqual(d.plan(candidate(),[],small,self.entries)['status'],'BLOCK')
        bb=d.render([{'version':'1.0','title':'Literal [b]',
                    'changes':[{'id':'a','text':'Corrigido texto [tag].','audience':'public'}]}],'bbcode')
        self.assertIn('&#91;tag&#93;',bb)
        self.assertIn('[tag]',d.changelog('## v1 — Title\n- Corrigido texto [tag].')[0]['changes'][0]['text'])
        with self.assertRaises(ValueError):d.changelog('## v1 — X\n- <script>alert(1)</script>')
        with self.assertRaises(ValueError):d.changelog('## v1 — X\n- Something\n## v1 — Y\n- Something')
        literal='Use `[label](https://example.invalid)` como texto literal.'
        self.assertEqual(d.plain_inline(literal),'Use [label](https://example.invalid) como texto literal.')
        combo=r'Preserve \*literal\*, **bold**, *emphasis*, `x_[y]` and [docs](https://example.invalid/a). ✓'
        self.assertEqual(d.plain_inline(combo),'Preserve *literal*, bold, emphasis, x_[y] and docs (https://example.invalid/a). ✓')
        with self.assertRaisesRegex(ValueError,'Unclosed inline code'):d.changelog('## v1 — X\n- Broken `code')
        with self.assertRaisesRegex(ValueError,'Unclosed emphasis'):d.changelog('## v1 — X\n- Broken **bold')

    def test_unsupported_markdown_links_and_images_fail_closed(self):
        for note in ('[click](http://example.invalid)', '[click](javascript:alert)',
                     '![track](https://example.invalid/pixel)', '[click](relative/path)',
                     '*![track](https://example.invalid/pixel)*',
                     '**[click](javascript:alert)**',
                     '[![track](https://example.invalid/pixel)](https://example.invalid)'):
            with self.subTest(note=note), self.assertRaises(ValueError):
                d.changelog('## v1 — X\n- '+note)
        self.assertEqual(d.plain_inline(r'Literal \[click](http://example.invalid)'),
                         'Literal [click](http://example.invalid)')

    def test_missing_change_and_new_target(self):
        c=candidate();c['included_changes'].append('#missing/1')
        self.assertEqual(d.plan(c,[],target(),self.entries)['status'],'BLOCK')
        self.assertEqual(d.plan(candidate(),[],target('nexus'),self.entries)['status'],'READY')
        missing_version=candidate();missing_version['version']='1.4'
        self.assertIn('no canonical changelog entry',d.plan(missing_version,[],target(),self.entries)['reason'])
        incomplete=candidate();incomplete['included_changes'].remove('#42/1')
        self.assertIn('formalized version entry',d.plan(incomplete,[],target(),self.entries)['reason'])

    def test_candidate_cannot_claim_changes_from_later_history_entries(self):
        earlier=candidate()
        earlier['version']='1.2'
        earlier['integration_order']=2
        blocked=d.plan(earlier,[],target(),self.entries)
        self.assertEqual(blocked['status'],'BLOCK')
        self.assertIn('later or missing changelog change',blocked['reason'])
        same=receipt('1.2',2,earlier['included_changes'])
        same.update(candidate_id=d.identity(earlier),
                    artifact_sha256=earlier['artifacts']['github'])
        self.assertEqual(d.plan(earlier,[same],target(),self.entries)['status'],'BLOCK')
        earlier['included_changes']=['#40/1','#41/1']
        ready=d.plan(earlier,[],target(),self.entries)
        self.assertEqual(ready['status'],'READY')
        self.assertEqual(ready['new_change_ids'],['#40/1','#41/1'])
        self.assertNotIn('v1.3',ready['notes'])

    def test_internal_version_and_skipped_versions_keep_canonical_history(self):
        internal={'version':'1.1','source_commit':'b'*40,'payload_sha256':'c'*64,
                  'artifacts':{'github':'d'*64},'included_changes':['#40/1'],'integration_order':1}
        result=d.plan(internal,[],target(),self.entries)
        self.assertEqual(result['status'],'READY')
        self.assertEqual(result['notes'],'')
        baseline=receipt('1.1',1,['#40/1'])
        later=d.plan(candidate(),[baseline],target(baseline='unknown'),self.entries)
        self.assertEqual(later['included_changes'],candidate()['included_changes'])
        self.assertEqual(later['new_change_ids'],['#41/1','#42/1'])


if __name__=='__main__':unittest.main()
