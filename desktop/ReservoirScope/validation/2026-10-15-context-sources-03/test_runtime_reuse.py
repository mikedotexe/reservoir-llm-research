"""File-only equivalence checks; the only operational policy change is 35 to 30%."""
import json
from pathlib import Path
import unittest
import prepare_window as prep
import prepare_inputs as prepared
import run_probe as probe
import admit_once as admission

HERE = Path(__file__).resolve().parent
OLD = prep.OLD


class RuntimeReuseTests(unittest.TestCase):
    def test_exact_supervisor_renderer_source_audit_and_reading_criteria(self):
        for name in prep.EXACT:
            self.assertEqual((HERE / name).read_bytes(), (OLD / name).read_bytes(), name)

    def test_runner_preparation_analysis_only_named_window_changes(self):
        count = len(json.loads((HERE / 'runtime-copy-01.json').read_text())['priorDirectoryAfter'])
        for name in prep.ADAPTED:
            self.assertEqual((HERE / name).read_bytes(), prep.adapted(name, count), name)

    def test_plan_preserves_model_request_bounds_and_only_declared_policy_change(self):
        plan = json.loads((HERE / 'run-plan.json').read_text()); old = json.loads((OLD / 'run-plan.json').read_text())
        for key in old.keys() - {'episodeId', 'ownedServiceDirectory', 'provenance'}:
            self.assertEqual(plan[key], old[key], key)
        original_policy = dict(old['provenance']['hostAdmission']); original_policy['minimumFreePercent'] = 30
        self.assertEqual(plan['provenance']['hostAdmission'], original_policy)
        self.assertEqual(original_policy, admission.POLICY)
        changed = {'authorization', 'resultsDirectory', 'hostAdmission', 'preAdmissionCleanupReceipt',
                   'priorAttempt', 'priorFrozenInputs', 'runtimeInterpretation'}
        for key in old['provenance'].keys() - changed:
            self.assertEqual(plan['provenance'][key], old['provenance'][key], key)
        self.assertEqual(set(plan['provenance']) - set(old['provenance']),
                         {'admissionPolicyId', 'admissionRationale', 'priorAttempts'})
        self.assertEqual(plan['provenance']['preAdmissionCleanupReceipt'], prep.identity(HERE / 'cleanup-result-01.json'))
        self.assertEqual(probe.ORDER, prepared.ORDER)

    def test_same_explicit_software_model_and_stage_identity(self):
        doc = json.loads(prep.SOFTWARE.read_text()); software = doc['installedSoftware']
        self.assertEqual(probe.OVERLAY_SHA, prep.identity(prep.SOFTWARE)['sha256'])
        self.assertEqual(probe.EXECUTABLE_SHA, software['executableSha256'])
        self.assertEqual(probe.PLIST_SHA, software['plistSha256'])
        self.assertEqual(software['CFBundleShortVersionString'], '0.40.5')
        self.assertEqual(doc['modelSelectionSha256'], probe.SELECTION_SHA)
        self.assertEqual(doc['stageReceiptSha256'], probe.STAGE_SHA)

    def test_twelve_prompt_bytes_order_and_original_candidate_exact(self):
        new = json.loads((HERE / 'frozen-inputs.json').read_text()); old = json.loads((OLD / 'frozen-inputs.json').read_text())
        self.assertEqual(new['runPlan'], prep.identity(HERE / 'run-plan.json')); self.assertEqual(len(new['slots']), 12)
        for current, previous in zip(new['slots'], old['slots']):
            for key in ('slot', 'anchorStep', 'condition'):
                self.assertEqual(current[key], previous[key])
            self.assertEqual(Path(current['prompt']['path']).read_bytes(), Path(previous['prompt']['path']).read_bytes())
            self.assertEqual(current['prompt'], prep.identity(current['prompt']['path']))
        transform = json.loads((HERE / 'transformation-checks-01.json').read_text())
        self.assertEqual(transform['candidateId'], 'context-sources-01')
        self.assertFalse(transform['productionVerifierExecuted']); self.assertFalse(transform['numericalValuesRecomputed'])
        self.assertTrue(transform['originalUnchanged']); self.assertEqual(transform['prompts'], new['slots'])

    def test_both_refusals_and_all_prior_validation_bytes_unchanged(self):
        copied = json.loads((HERE / 'runtime-copy-01.json').read_text())
        self.assertEqual(copied['priorDirectoryBefore'], copied['priorDirectoryAfter'])
        for ref in copied['priorDirectoryAfter'] + copied['priorQualification']:
            self.assertEqual(ref, prep.identity(ref['path']))
        plan = json.loads((HERE / 'run-plan.json').read_text())
        self.assertEqual(len(plan['provenance']['priorAttempts']), 2)
        for ref in plan['provenance']['priorAttempts']:
            self.assertEqual(ref, prep.identity(ref['path']))
        old_plan = json.loads((OLD / 'run-plan.json').read_text())
        old_admission = json.loads((OLD / 'host-admission-01.json').read_text())
        self.assertEqual(old_plan['provenance']['hostAdmission']['minimumFreePercent'], 35)
        self.assertEqual(old_admission['freePercent'], 31)
        self.assertFalse(old_admission['admitted'])
        self.assertEqual(len(copied['priorDirectoryAfter']), 492)

    def test_runner_accepts_only_bound_new_inputs(self):
        path = HERE / 'frozen-inputs.json'
        plan, doc, prompts, refs = probe.load_inputs(path, prep.identity(path)['sha256'])
        self.assertEqual(plan['episodeId'], 'context-sources-03'); self.assertEqual(len(prompts), 12)
        probe.verify_refs(refs)
        with self.assertRaises(ValueError): probe.load_inputs(path, '0' * 64)


if __name__ == '__main__':
    unittest.main()
