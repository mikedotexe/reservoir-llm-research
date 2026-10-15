"""File-only source-equivalence and input gates; no sockets or host queries."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import prepare_inputs as prepared

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'2026-10-15-time-direction-03'

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value

p=module('context_probe','run_probe.py')
f=module('context_freeze','freeze_inputs.py')

class RuntimeReuseTests(unittest.TestCase):
    def test_runner_and_test_only_namespace_and_owned_path_changes(self):
        for name in ('run_probe.py','test_run_probe.py'):
            old=(OLD/name).read_text().replace('time-direction','context-sources').replace('context-sources-gemma3-4b-run03','context-sources-gemma3-4b-run01')
            self.assertEqual((HERE/name).read_text(),old)

    def test_supervisor_exact_renderer_only_schema_names(self):
        for name in ('owned_model.py','test_owned_model.py'):
            self.assertEqual((HERE/name).read_bytes(),(OLD/name).read_bytes())
        for name in ('render_blind_pack.py','test_render_blind_pack.py'):
            self.assertEqual((HERE/name).read_text(),(OLD/name).read_text().replace('time-direction','context-sources'))

    def test_admission_only_episode_name_changed(self):
        self.assertEqual((HERE/'admit_once.py').read_text(),(OLD/'admit_once.py').read_text().replace('time-direction-03','context-sources-01'))

    def test_all_runtime_bounds_model_anchors_and_order_exact(self):
        plan=json.loads((HERE/'run-plan.json').read_text());old=json.loads((OLD/'run-plan.json').read_text())
        for key in old.keys()-{'schema','episodeId','ownedServiceDirectory','provenance'}:self.assertEqual(plan[key],old[key])
        for key in ('anchors','hostAdmission','maxFreshRequests','automaticRetries','manualRetries','replaceFailedSamples'):
            self.assertEqual(plan['provenance'][key],old['provenance'][key])
        self.assertEqual(plan['provenance']['candidateParagraph'],prepared.PARAGRAPH)
        self.assertEqual(plan['provenance']['preAdmissionCleanupReceipt'],f.identity(HERE/'cleanup-result-01.json'))
        self.assertEqual(p.ORDER,prepared.ORDER)
        self.assertTrue(plan['ownedServiceDirectory'].endswith('/target/qa/0.20-context-sources-gemma3-4b-run01'))
        self.assertTrue(plan['provenance']['resultsDirectory'].endswith('/target/qa/0.20-context-sources-results01'))

    def test_all_twelve_inputs_and_exact_transformation_receipt(self):
        doc=json.loads((HERE/'frozen-inputs.json').read_text());transform=json.loads((HERE/'transformation-checks-01.json').read_text())
        self.assertEqual(doc['slots'],transform['prompts']);self.assertEqual(len(doc['slots']),12)
        self.assertEqual(doc['runPlan'],f.identity(HERE/'run-plan.json'))
        self.assertEqual(doc['provenance']['transformation'],f.identity(HERE/'transformation-checks-01.json'))
        for slot in doc['slots']:self.assertEqual(slot['prompt'],f.identity(slot['prompt']['path']))
        self.assertFalse(transform['productionVerifierExecuted'])
        self.assertFalse(transform['numericalValuesRecomputed'])

    def test_all_prior_evidence_and_qualification_unchanged(self):
        copied=json.loads((HERE/'runtime-copy-01.json').read_text())
        self.assertEqual(copied['priorDirectoryBefore'],copied['priorDirectoryAfter'])
        for ref in copied['priorDirectoryAfter']+copied['priorQualification']:self.assertEqual(ref,f.identity(ref['path']))
        self.assertEqual(copied['sourceEpisodeFileCount'],100)
        self.assertEqual(copied['inheritedPriorFileCount'],285)

    def test_copied_inputs_load_and_tampered_hash_refuses(self):
        path=HERE/'frozen-inputs.json';plan,doc,prompts,refs=p.load_inputs(path,f.identity(path)['sha256'])
        self.assertEqual(plan['episodeId'],'context-sources-01');self.assertEqual(len(prompts),12)
        self.assertEqual([(s['anchorStep'],s['condition']) for s in doc['slots']],p.ORDER)
        p.verify_refs(refs)
        with self.assertRaises(ValueError):p.load_inputs(path,'0'*64)

    def test_freeze_requires_root_cleanup_and_identity_bound_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            for name in ('PROTOCOL.md','READING-PROTOCOL.md','PRE-RUN-REVIEW.md'):(root/name).write_text('Synthetic document.')
            review=dict(status='no_concrete_blocker_found',review=f.identity(root/'PRE-RUN-REVIEW.md'),reviewedFiles=[f.identity(root/'PROTOCOL.md')])
            (root/'pre-run-review-01.json').write_text(json.dumps(review))
            with self.assertRaises(FileNotFoundError):f.required_documents(root)
            (root/'cleanup-result-01.json').write_text(json.dumps(dict(status='no_app_changes')))
            f.required_documents(root)
            (root/'PROTOCOL.md').write_text('Changed after review.')
            with self.assertRaises(AssertionError):f.required_documents(root)
            (root/'pre-run-review-01.json').unlink()
            with self.assertRaises(FileNotFoundError):f.required_documents(root)

if __name__=='__main__':unittest.main()
