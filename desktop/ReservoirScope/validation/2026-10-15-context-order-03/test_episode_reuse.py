"""File-only adaptation checks. No network, model, admission or process queries."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'2026-10-14-context-order-02'
SPEC=importlib.util.spec_from_file_location('reused_probe',HERE/'run_probe.py')
probe=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(probe)

def identity(p):
    raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

class ReuseTests(unittest.TestCase):
    def test_only_runner_owned_basename_and_test_fixture_changed(self):
        for name,count in [('run_probe.py',2),('test_run_probe.py',1)]:
            old=(OLD/name).read_text();new=(HERE/name).read_text()
            self.assertEqual(old.count('0.20-context-order-gemma3-4b-run02'),count)
            self.assertEqual(new,old.replace('0.20-context-order-gemma3-4b-run02','0.20-context-order-gemma3-4b-run03'))
    def test_supervisor_renderer_reading_and_tests_exact(self):
        for name in ['owned_model.py','test_owned_model.py','render_blind_pack.py','test_render_blind_pack.py','READING-PROTOCOL.md']:
            with self.subTest(name=name):self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes())
    def test_all_twelve_prompts_and_order_exact(self):
        old=json.loads((OLD/'frozen-inputs.json').read_text());new=json.loads((HERE/'frozen-inputs.json').read_text())
        self.assertEqual(len(new['slots']),12)
        for a,b in zip(old['slots'],new['slots']):
            self.assertEqual({k:v for k,v in a.items() if k!='prompt'},{k:v for k,v in b.items() if k!='prompt'})
            self.assertEqual(Path(a['prompt']['path']).read_bytes(),Path(b['prompt']['path']).read_bytes())
            self.assertEqual(identity(Path(b['prompt']['path'])),b['prompt'])
        plan,doc,prompts,refs=probe.load_inputs(HERE/'frozen-inputs.json',identity(HERE/'frozen-inputs.json')['sha256'])
        self.assertEqual(doc['episodeId'],'context-order-03');self.assertEqual(len(prompts),12)
    def test_all_limits_and_software_model_unchanged(self):
        old=json.loads((OLD/'run-plan.json').read_text());new=json.loads((HERE/'run-plan.json').read_text())
        for k,v in old.items():
            if k not in ('episodeId','ownedServiceDirectory','provenance'):self.assertEqual(new[k],v)
        self.assertEqual(new['ownedServiceDirectory'],old['ownedServiceDirectory'].replace('run02','run03'))
        for k,v in old['provenance'].items():
            if k not in ('priorRefusal','authorization','resultsDirectory'):self.assertEqual(new['provenance'][k],v)
        self.assertEqual(len(new['provenance']['priorRefusals']),2)
        self.assertTrue(new['provenance']['resultsDirectory'].endswith('/target/qa/0.20-context-order-results03'))
    def test_admission_only_episode_identifier_changed(self):
        self.assertEqual((HERE/'admit_once.py').read_text(),(OLD/'admit_once.py').read_text().replace('"context-order-02"','"context-order-03"'))
    def test_prior_directory_and_refusal_bindings_unchanged(self):
        copied=json.loads((HERE/'copy-manifest-01.json').read_text())
        before=copied['priorDirectoryBefore'];after=copied['priorDirectoryAfter']
        self.assertEqual(before,after);self.assertEqual(after,[identity(Path(r['path'])) for r in after])
        self.assertEqual(copied['priorBindings'],[identity(Path(r['path'])) for r in copied['priorBindings']])
        for prior in ('2026-10-14-context-order-01','2026-10-14-context-order-02'):
            refused=json.loads((HERE.parent/prior/'outcome-01.json').read_text())
            self.assertEqual(refused['status'],'closed_admission_refused');self.assertTrue(all(s['status']=='unstarted' for s in refused['slots']))

if __name__=='__main__':unittest.main()
