"""File-only equivalence tests for a new explicitly selected runtime window."""
import importlib.util
import json
from pathlib import Path
import unittest
import prepare_window as prep
import prepare_inputs as prepared
import run_probe as probe

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'2026-10-15-context-sources-01'

def ident(p):return prep.identity(p)
class RuntimeReuseTests(unittest.TestCase):
 def test_only_declared_runtime_guard_and_window_changes(self):
  software=json.loads(prep.SOFTWARE.read_text());copied=json.loads((HERE/'runtime-copy-01.json').read_text())
  for name in ('run_probe.py','test_run_probe.py','admit_once.py','prepare_inputs.py','retain_and_analyze.py'):
   value=(OLD/name).read_text()
   for old,new in prep.replacements(software):value=value.replace(old,new)
   if name=='prepare_inputs.py':value=value.replace("candidateId='context-sources-02'","candidateId='context-sources-01'")
   if name=='retain_and_analyze.py':value=value.replace('len(prior)==385',f"len(prior)=={len(copied['priorDirectoryAfter'])}")
   self.assertEqual((HERE/name).read_text(),value,name)
 def test_supervisor_renderer_preparation_tests_and_audit_exact(self):
  for name in ('owned_model.py','test_owned_model.py','render_blind_pack.py','test_render_blind_pack.py','test_prepare_inputs.py','audit_source_context.py','READING-PROTOCOL.md'):
   self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes(),name)
 def test_runtime_selection_matches_all_literal_guards(self):
  doc=json.loads(prep.SOFTWARE.read_text());s=doc['installedSoftware']
  self.assertEqual(probe.OVERLAY_SHA,ident(prep.SOFTWARE)['sha256'])
  self.assertEqual(probe.EXECUTABLE_SHA,s['executableSha256']);self.assertEqual(probe.PLIST_SHA,s['plistSha256'])
  self.assertEqual(s['CFBundleShortVersionString'],'0.40.5');self.assertEqual(doc['modelSelectionSha256'],probe.SELECTION_SHA)
  self.assertEqual(doc['stageReceiptSha256'],probe.STAGE_SHA)
 def test_all_model_request_resource_bounds_unchanged(self):
  plan=json.loads((HERE/'run-plan.json').read_text());old=json.loads((OLD/'run-plan.json').read_text())
  for key in old.keys()-{'episodeId','ownedServiceDirectory','softwareSelectionPath','softwareSelectionSha256','provenance'}:self.assertEqual(plan[key],old[key],key)
  for key in ('anchors','hostAdmission','maxFreshRequests','automaticRetries','manualRetries','replaceFailedSamples','candidateParagraph','candidateId'):self.assertEqual(plan['provenance'][key],old['provenance'][key])
  self.assertEqual(plan['provenance']['preAdmissionCleanupReceipt'],ident(HERE/'cleanup-result-01.json'))
  self.assertEqual(probe.ORDER,prepared.ORDER)
 def test_exact_twelve_frozen_prompts_and_original_transformation(self):
  new=json.loads((HERE/'frozen-inputs.json').read_text());old=json.loads((OLD/'frozen-inputs.json').read_text())
  self.assertEqual(new['runPlan'],ident(HERE/'run-plan.json'));self.assertEqual(len(new['slots']),12)
  for a,b in zip(new['slots'],old['slots']):
   for key in ('slot','anchorStep','condition'):self.assertEqual(a[key],b[key])
   self.assertEqual(Path(a['prompt']['path']).read_bytes(),Path(b['prompt']['path']).read_bytes())
   self.assertEqual(a['prompt'],ident(a['prompt']['path']))
  tr=json.loads((HERE/'transformation-checks-01.json').read_text())
  self.assertEqual(tr['candidateId'],'context-sources-01');self.assertFalse(tr['productionVerifierExecuted']);self.assertFalse(tr['numericalValuesRecomputed'])
  self.assertTrue(tr['originalUnchanged']);self.assertEqual(tr['prompts'],new['slots'])
 def test_prior_refusal_and_evidence_intact(self):
  copied=json.loads((HERE/'runtime-copy-01.json').read_text())
  self.assertEqual(copied['priorDirectoryBefore'],copied['priorDirectoryAfter'])
  for ref in copied['priorDirectoryAfter']+copied['priorQualification']:self.assertEqual(ref,ident(ref['path']))
  freeze=json.loads((OLD/'evaluation-freeze-01.json').read_text())
  for ref in freeze['files']:self.assertEqual(ref,ident(ref['path']))
  self.assertEqual(len(copied['priorDirectoryAfter']),438)
 def test_runner_loads_only_exact_new_inputs(self):
  path=HERE/'frozen-inputs.json';plan,doc,prompts,refs=probe.load_inputs(path,ident(path)['sha256'])
  self.assertEqual(plan['episodeId'],'context-sources-02');self.assertEqual(len(prompts),12);probe.verify_refs(refs)
  with self.assertRaises(ValueError):probe.load_inputs(path,'0'*64)
if __name__=='__main__':unittest.main()
