import importlib.util
from pathlib import Path
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


def receipt(version,order,changes,id='github',status='confirmed'):
    return {'schema':'bootcrate-receipt/v1','destination':id,'channel':'stable','version':version,
            'integration_order':order,'included_changes':changes,'status':status,
            'attempt_id':'attempt-'+id+'-'+version,
            'candidate_id':'old','artifact_sha256':'e'*64,'evidence_ref':'https://example.invalid/release',
            'observed_by':'authorized operator','observed_at':'2026-09-24T00:00:00Z'}


class DeliveryTests(unittest.TestCase):
    def setUp(self):self.entries=d.changelog(SOURCE)

    def test_bootcrate_itself_keeps_integrated_version_history(self):
        source=Path(__file__).resolve().parents[4]/'CHANGELOG.md'
        versions=[entry['version'] for entry in d.changelog(source.read_text())]
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

    def test_baseline_independent_and_internal_note_filtered(self):
        old=receipt('1.1',1,['#40/1']);ahead=receipt('1.2',2,['#40/1','#41/1'],id='nexus')
        github=d.plan(candidate(),[old,ahead],target('github',baseline='unknown'),self.entries)
        nexus=d.plan(candidate(),[old,ahead],target('nexus',baseline='unknown'),self.entries)
        self.assertEqual(hub:=github['included_changes'],['#41/1','#42/1'])
        self.assertEqual(nexus['included_changes'],['#42/1'])
        self.assertIn('CSV',github['notes']);self.assertNotIn('configurações',github['notes'])
        self.assertNotIn('CSV',nexus['notes'])

    def test_unknown_partial_and_duplicate_behaviors(self):
        self.assertEqual(d.plan(candidate(),[],target(baseline='unknown'),self.entries)['status'],'BLOCK')
        self.assertEqual(d.plan(candidate(),[receipt('1.2',2,['#40/1','#41/1'],status='unknown')],target(),self.entries)['status'],'BLOCK')
        same=receipt('1.3',3,candidate()['included_changes']);same['candidate_id']=d.identity(candidate());same['artifact_sha256']='c'*64
        self.assertEqual(d.plan(candidate(),[same],target(),self.entries)['status'],'SKIP')
        same['artifact_sha256']='d'*64
        self.assertEqual(d.plan(candidate(),[same],target(),self.entries)['status'],'BLOCK')
        unresolved=receipt('1.3',3,candidate()['included_changes'],status='unknown')
        resolved={**unresolved,'status':'confirmed','candidate_id':d.identity(candidate()),'artifact_sha256':'c'*64}
        self.assertEqual(d.plan(candidate(),[unresolved,resolved],target(),self.entries)['status'],'SKIP')
        later=receipt('1.4',4,candidate()['included_changes'])
        self.assertEqual(d.plan(candidate(),[resolved,later],target(),self.entries)['status'],'BLOCK')

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

    def test_missing_change_and_new_target(self):
        c=candidate();c['included_changes'].append('#missing/1')
        self.assertEqual(d.plan(c,[],target(),self.entries)['status'],'BLOCK')
        self.assertEqual(d.plan(candidate(),[],target('nexus'),self.entries)['status'],'READY')


if __name__=='__main__':unittest.main()
