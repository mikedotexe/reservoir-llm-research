"""Focused file-only episode reuse tests. No sockets, host probes or processes."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '2026-10-15-time-direction-02'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


p = module('reuse_probe', 'run_probe.py')
f = module('reuse_freeze', 'freeze_inputs.py')


class RuntimeReuseTests(unittest.TestCase):
    def test_runner_only_changes_owned_basename(self):
        for name, count in [('run_probe.py', 2), ('test_run_probe.py', 1)]:
            old = (OLD / name).read_text()
            self.assertEqual(old.count('0.20-time-direction-gemma3-4b-run02'), count)
            self.assertEqual((HERE / name).read_text(), old.replace('0.20-time-direction-gemma3-4b-run02', '0.20-time-direction-gemma3-4b-run03'))

    def test_supervisor_renderer_and_reading_criteria_byte_exact(self):
        for name in ['owned_model.py', 'test_owned_model.py', 'render_blind_pack.py', 'test_render_blind_pack.py', 'READING-PROTOCOL.md']:
            self.assertEqual((HERE / name).read_bytes(), (OLD / name).read_bytes())

    def test_admission_only_changes_recorded_episode(self):
        old = (OLD / 'admit_once.py').read_text()
        self.assertEqual(old.count('"time-direction-02"'), 1)
        self.assertEqual((HERE / 'admit_once.py').read_text(), old.replace('"time-direction-02"', '"time-direction-03"'))

    def test_all_bounds_conditions_and_order_unchanged(self):
        plan = json.loads((HERE / 'run-plan.json').read_text())
        old = json.loads((OLD / 'run-plan.json').read_text())
        for key in old.keys() - {'episodeId', 'ownedServiceDirectory', 'provenance'}:
            self.assertEqual(plan[key], old[key])
        for key in ['anchors', 'selection', 'conditions', 'maxFreshRequests', 'automaticRetries', 'manualRetries', 'replaceFailedSamples', 'hostAdmission', 'sourcePromptVersion', 'sourceEpisode']:
            self.assertEqual(plan['provenance'][key], old['provenance'][key])
        self.assertEqual(plan['episodeId'], 'time-direction-03')
        self.assertEqual(plan['ownedServiceDirectory'], old['ownedServiceDirectory'].replace('run02', 'run03'))
        self.assertEqual(plan['provenance']['resultsDirectory'], old['provenance']['resultsDirectory'].replace('results02', 'results03'))
        self.assertEqual(plan['provenance']['priorRefusal'], f.identity(OLD / 'outcome-01.json'))
        self.assertEqual(plan['provenance']['preAdmissionCleanupReceipt'], f.identity(HERE / 'cleanup-result-01.json'))
        self.assertFalse(plan['provenance']['otherApplicationsChangedDuringProbe'])
        self.assertFalse(plan['provenance']['BeingsOrSharedServicesTouched'])
        self.assertNotIn('otherApplicationsOrBeingsTouched', plan['provenance'])

    def test_all_twelve_prompts_and_source_provenance_exact(self):
        doc = json.loads((HERE / 'frozen-inputs.json').read_text())
        old = json.loads((OLD / 'frozen-inputs.json').read_text())
        self.assertEqual(len(doc['slots']), 12)
        for new, previous in zip(doc['slots'], old['slots']):
            self.assertEqual({k: v for k, v in new.items() if k != 'prompt'}, {k: v for k, v in previous.items() if k != 'prompt'})
            self.assertEqual(Path(new['prompt']['path']).read_bytes(), Path(previous['prompt']['path']).read_bytes())
            self.assertEqual(new['prompt'], f.identity(new['prompt']['path']))
        for key, value in old['provenance'].items():
            if key not in ('reusedInputs', 'priorRefusal'):
                self.assertEqual(doc['provenance'][key], value)
        self.assertEqual(doc['provenance']['reusedInputs'], f.identity(OLD / 'frozen-inputs.json'))
        self.assertEqual(doc['provenance']['priorRefusal'], f.identity(OLD / 'outcome-01.json'))
        self.assertFalse(doc['provenance']['promptsRegenerated'])
        self.assertEqual(doc['runPlan'], f.identity(HERE / 'run-plan.json'))

    def test_all_prior_files_and_qualification_unchanged(self):
        copied = json.loads((HERE / 'runtime-copy-01.json').read_text())
        self.assertEqual(copied['priorDirectoryBefore'], copied['priorDirectoryAfter'])
        for ref in copied['priorDirectoryAfter'] + copied['priorQualification']:
            self.assertEqual(ref, f.identity(ref['path']))
        self.assertEqual(copied['sourceEpisodeFileCount'], 41)
        self.assertEqual(copied['inheritedPriorFileCount'], 244)

    def test_copied_inputs_load_and_tampered_identity_refuses(self):
        path = HERE / 'frozen-inputs.json'
        plan, doc, prompts, refs = p.load_inputs(path, f.identity(path)['sha256'])
        self.assertEqual(plan['episodeId'], 'time-direction-03')
        self.assertEqual([(s['anchorStep'], s['condition']) for s in doc['slots']], p.ORDER)
        self.assertEqual(len(prompts), 12)
        p.verify_refs(refs)
        with self.assertRaises(ValueError):
            p.load_inputs(path, '0' * 64)

    def test_freeze_requires_cleanup_and_identity_bound_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name in ['PROTOCOL.md', 'READING-PROTOCOL.md', 'PRE-RUN-REVIEW.md']:
                (root / name).write_text('Synthetic document.')
            review = dict(status='no_concrete_blocker_found', review=f.identity(root / 'PRE-RUN-REVIEW.md'), reviewedFiles=[f.identity(root / 'PROTOCOL.md')])
            (root / 'pre-run-review-01.json').write_text(json.dumps(review))
            with self.assertRaises(FileNotFoundError):
                f.required_documents(root)
            (root / 'cleanup-result-01.json').write_text(json.dumps(dict(status='no_safe_closures', applied=False)))
            f.required_documents(root)
            (root / 'PROTOCOL.md').write_text('Changed after review.')
            with self.assertRaises(AssertionError):
                f.required_documents(root)
            (root / 'pre-run-review-01.json').unlink()
            with self.assertRaises(FileNotFoundError):
                f.required_documents(root)


if __name__ == '__main__':
    unittest.main()
