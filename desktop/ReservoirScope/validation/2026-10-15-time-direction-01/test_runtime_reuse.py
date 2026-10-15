"""File/temp-file-only namespace/anchor checks. No service, host, socket or model actions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'2026-10-15-context-order-03'
SPEC=importlib.util.spec_from_file_location('time_probe',HERE/'run_probe.py')
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)

def ident(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

class RuntimeReuseTests(unittest.TestCase):
    def test_runner_transport_unchanged_outside_declared_literals(self):
        for name in ['run_probe.py','test_run_probe.py']:
            old=(OLD/name).read_text().replace('context-order','time-direction').replace('gemma3-4b-run03','gemma3-4b-run01')
            if name=='run_probe.py':old=old.replace('enumerate(range(60,361,60))','enumerate((30,60,90,120,330,360))')
            self.assertEqual((HERE/name).read_text(),old)
    def test_renderer_logic_unchanged_outside_schema_and_anchors(self):
        for name in ['render_blind_pack.py','test_render_blind_pack.py']:
            old=(OLD/name).read_text().replace('context-order','time-direction').replace('enumerate(range(60, 361, 60))','enumerate((30, 60, 90, 120, 330, 360))')
            if name=='test_render_blind_pack.py':old=old.replace('["anchorStep"], 60)','["anchorStep"], 30)')
            self.assertEqual((HERE/name).read_text(),old)
    def test_supervisor_exact_and_admission_only_episode_id_changed(self):
        for name in ['owned_model.py','test_owned_model.py']:self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes())
        self.assertEqual((HERE/'admit_once.py').read_text(),(OLD/'admit_once.py').read_text().replace('"context-order-03"','"time-direction-01"'))
    def test_same_limits_model_and_runtime_plan(self):
        plan=json.loads((HERE/'run-plan.json').read_text());old=json.loads((OLD/'run-plan.json').read_text())
        for key,value in old.items():
            if key not in ('schema','episodeId','ownedServiceDirectory','provenance'):self.assertEqual(plan[key],value)
        self.assertEqual(plan['schema'],'reservoir-time-direction-plan-v1');self.assertEqual(plan['episodeId'],'time-direction-01')
        self.assertTrue(plan['ownedServiceDirectory'].endswith('/target/qa/0.20-time-direction-gemma3-4b-run01'))
        self.assertTrue(plan['provenance']['resultsDirectory'].endswith('/target/qa/0.20-time-direction-results01'))
        self.assertEqual(p.ORDER,[(30,'A'),(30,'B'),(60,'B'),(60,'A'),(90,'A'),(90,'B'),(120,'B'),(120,'A'),(330,'A'),(330,'B'),(360,'B'),(360,'A')])
    def test_all_three_prior_folders_unchanged(self):
        refs=json.loads((HERE/'runtime-copy-01.json').read_text())
        self.assertEqual(refs['priorDirectoryBefore'],refs['priorDirectoryAfter'])
        self.assertEqual(refs['priorDirectoryAfter'],[ident(Path(x['path'])) for x in refs['priorDirectoryAfter']])
        self.assertEqual(len(refs['priorEpisodes']),3)
        self.assertEqual(refs['priorQualification'],[ident(Path(x['path'])) for x in refs['priorQualification']])
    def test_synthetic_inputs_accept_new_anchors_reject_old_order_or_schema(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();plan=dict(p.BOUNDS,schema='reservoir-time-direction-plan-v1',episodeId='test');pp=root/'plan.json';pp.write_bytes(p.encoded(plan));slots=[]
            for i,(step,c) in enumerate(p.ORDER,1):
                path=root/f'prompt-{i}.txt';path.write_text('Synthetic unchanged context.')
                slots.append(dict(slot=i,anchorStep=step,condition=c,prompt=ident(path)))
            doc=dict(schema='reservoir-time-direction-inputs-v1',episodeId='test',runPlan=ident(pp),slots=slots)
            ip=root/'inputs.json';ip.write_bytes(p.encoded(doc))
            self.assertEqual(len(p.load_inputs(ip,ident(ip)['sha256'])[2]),12)
            doc['slots'][0]['anchorStep']=60;ip.write_bytes(p.encoded(doc))
            with self.assertRaises(ValueError):p.load_inputs(ip,ident(ip)['sha256'])
            doc['slots'][0]['anchorStep']=30;doc['schema']='reservoir-context-order-inputs-v1';ip.write_bytes(p.encoded(doc))
            with self.assertRaises(ValueError):p.load_inputs(ip,ident(ip)['sha256'])

if __name__=='__main__':unittest.main()
