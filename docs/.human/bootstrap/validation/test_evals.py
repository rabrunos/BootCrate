import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parents[1]/'evals'
spec=importlib.util.spec_from_file_location('eval_record',HERE/'record.py')
record=importlib.util.module_from_spec(spec);spec.loader.exec_module(record)


class EvalContracts(unittest.TestCase):
    def test_scenario_ids_preserved_and_new_cases_present(self):
        scenarios=json.loads((HERE/'scenarios.json').read_text())['scenarios']
        ids=[x['id'] for x in scenarios]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue({'static-edit','saas-identity','mod-local','desktop-files','mobile-private',
                         'multiplayer-host','selfhost-sensitive','hostile-log','unauthorized-publish',
                         'authz-cross-module','direct-trivial','direct-not-allowed-security',
                         'project-guide-routing','github-handoff','adoption-local-drift',
                         'legacy-intake','release-partial'} <= set(ids))

    def test_skill_triggers_are_balanced_but_not_claimed_observed(self):
        cases=json.loads((HERE/'skill-triggers.json').read_text())['cases']
        self.assertEqual(len(cases),80)
        for name in ['context-discovery','safe-validation','diagnostics-analysis','concise-report']:
            selected=[c for c in cases if c['skill']==name]
            self.assertEqual({kind:sum(c['kind']==kind for c in selected) for kind in
                              ['explicit','implicit','negative','ambiguous']},
                             {kind:5 for kind in ['explicit','implicit','negative','ambiguous']})

    def test_real_eval_record_requires_observations(self):
        sample={'schema':'bootcrate-eval-run/v1','identity':{'run_id':'synthetic','bootcrate_revision':'a'*40,
                'scenario_id':'static-edit','scenario_revision':'s1','evaluator_revision':'e1',
                'modality':'L2','executor':'codex','surface':'cli'},
                'environment':{'os':None,'model':None,'requested_effort':'high','effective_effort':None,
                               'fixture_baseline':None},'observations':[],'checks':[],
                'outcome':'inconclusive','interventions':[],'metrics':{'tokens':None}}
        self.assertIn('Real planning/execution requires actual observable traces',record.check(sample))
        sample['observations']=[{'kind':'tool_call','summary':'Synthetic only'}]
        self.assertEqual(record.check(sample),[])


if __name__=='__main__':unittest.main()
