"""Synthetic admission checks only: all entrypoint host queries are mocked."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import admit_once as a


def samples(free=20, pressure=1):
    return [dict(exit=0, stdout='68719476736\n'),
            dict(exit=0, stdout=f'{pressure}\n'),
            dict(exit=0, stdout=f'System-wide memory free percentage: {free}%\n')]


def identity(path):
    raw = path.read_bytes()
    return dict(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class AdmissionTests(unittest.TestCase):
    def frozen(self, root, *, policy=None, policy_id=a.POLICY_ID, episode=a.EPISODE_ID):
        plan = dict(episodeId=episode, provenance=dict(
            hostAdmission=dict(a.POLICY) if policy is None else policy,
            admissionPolicyId=policy_id))
        path = root / 'run-plan.json'
        path.write_text(json.dumps(plan) + '\n')
        (root / 'evaluation-freeze-01.json').write_text(json.dumps(dict(files=[identity(path)])))
        return path

    def assert_preflight_refuses(self, root, exception=ValueError):
        with patch.object(a.subprocess, 'run') as run, patch.object(a.shutil, 'disk_usage') as disk:
            with self.assertRaises(exception):
                a.main(root)
        run.assert_not_called()
        disk.assert_not_called()
        self.assertTrue((root / 'host-admission-01.json').exists())

    def test_19_refused_20_29_30_accepted(self):
        for free, expected in ((19, False), (20, True), (29, True), (30, True)):
            with self.subTest(free=free):
                self.assertEqual(a.decision(samples(free), 8 * 1024**3, a.POLICY)['admitted'], expected)

    def test_non_normal_pressure_refused(self):
        for level in (0, 2, 4):
            with self.subTest(level=level):
                self.assertFalse(a.decision(samples(80, level), 100 * 1024**3, a.POLICY)['admitted'])

    def test_disk_boundary_and_invalid_values(self):
        for free in (8 * 1024**3 - 1, None, '8589934592', True):
            self.assertFalse(a.decision(samples(), free, a.POLICY)['admitted'])
        self.assertTrue(a.decision(samples(), 8 * 1024**3, a.POLICY)['admitted'])

    def test_missing_failed_or_malformed_probe_refuses(self):
        cases = [[], samples()[:2]]
        for index in range(3):
            row = samples(); row[index] = dict(error='synthetic timeout'); cases.append(row)
            row = samples(); row[index]['exit'] = 1; cases.append(row)
            row = samples(); row[index]['stdout'] = 'unrecognized'; cases.append(row)
        for row in cases:
            with self.subTest(row=row):
                self.assertFalse(a.decision(row, 8 * 1024**3, a.POLICY)['admitted'])

    def test_ambiguous_percentage_and_zero_ram_refuse(self):
        for text in ('System-wide memory free percentage: 101%',
                     'System-wide memory free percentage: -1%',
                     'System-wide memory free percentage: 20%\nSystem-wide memory free percentage: 70%'):
            row = samples(); row[2]['stdout'] = text
            self.assertFalse(a.decision(row, 8 * 1024**3, a.POLICY)['admitted'])
        row = samples(); row[0]['stdout'] = '0'
        self.assertFalse(a.decision(row, 8 * 1024**3, a.POLICY)['admitted'])

    def test_changed_policy_not_silently_applied(self):
        for key, value in (('minimumFreePercent', 19), ('minimumFreePercent', 30),
                           ('requiredPressureLevel', 2), ('minimumFreeDiskBytes', 1), ('attempts', 2)):
            policy = dict(a.POLICY); policy[key] = value
            with self.assertRaisesRegex(ValueError, 'policy'):
                a.decision(samples(), 8 * 1024**3, policy)

    def test_entrypoint_records_bound_policy_and_exact_probe_sequence(self):
        for free, expected in ((19, False), (20, True), (29, True), (30, True)):
            with self.subTest(free=free), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.frozen(root)
                returns = [SimpleNamespace(returncode=x['exit'], stdout=x['stdout'], stderr='') for x in samples(free)]
                with patch.object(a.subprocess, 'run', side_effect=returns) as run, \
                     patch.object(a.shutil, 'disk_usage', return_value=SimpleNamespace(free=8 * 1024**3)) as disk, \
                     contextlib.redirect_stdout(io.StringIO()):
                    a.main(root)
                doc = json.loads((root / 'host-admission-01.json').read_text())
                self.assertEqual(doc['admitted'], expected)
                self.assertEqual(doc['policyId'], a.POLICY_ID)
                self.assertEqual(doc['episodeId'], a.EPISODE_ID)
                self.assertEqual(doc['thresholds'], a.POLICY)
                self.assertEqual(doc['runPlan'], identity(root / 'run-plan.json'))
                self.assertEqual(doc['freezeSha256'], identity(root / 'evaluation-freeze-01.json')['sha256'])
                self.assertEqual([c.args[0] for c in run.call_args_list], list(a.COMMANDS))
                self.assertTrue(all(c.kwargs['timeout'] == 10 for c in run.call_args_list))
                disk.assert_called_once_with(root)

    def test_existing_partial_receipt_prevents_any_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'host-admission-01.json').write_text('')
            self.assert_preflight_refuses(root, FileExistsError)

    def test_repeat_after_completed_refusal_or_acceptance_preserves_receipt(self):
        for free in (19, 20):
            with self.subTest(free=free), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.frozen(root)
                returns = [SimpleNamespace(returncode=x['exit'], stdout=x['stdout'], stderr='') for x in samples(free)]
                with patch.object(a.subprocess, 'run', side_effect=returns), \
                     patch.object(a.shutil, 'disk_usage', return_value=SimpleNamespace(free=8 * 1024**3)), \
                     contextlib.redirect_stdout(io.StringIO()):
                    a.main(root)
                before = (root / 'host-admission-01.json').read_bytes()
                self.assert_preflight_refuses(root, FileExistsError)
                self.assertEqual((root / 'host-admission-01.json').read_bytes(), before)

    def test_changed_plan_unbound_plan_and_changed_frozen_file_refuse(self):
        for kind in ('changed-plan', 'unbound-plan', 'changed-file'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); plan = self.frozen(root)
                freeze = root / 'evaluation-freeze-01.json'
                if kind == 'changed-plan':
                    plan.write_text(plan.read_text() + ' ')
                elif kind == 'unbound-plan':
                    freeze.write_text(json.dumps(dict(files=[])))
                else:
                    other = root / 'input.txt'; other.write_text('frozen')
                    freeze.write_text(json.dumps(dict(files=[identity(plan), identity(other)])))
                    other.write_text('changed')
                self.assert_preflight_refuses(root)

    def test_wrong_or_missing_policy_identity_refuses_before_probes(self):
        for policy_id in ('normal-pressure-reported-free-30-v1', 'unknown', None):
            with self.subTest(policy_id=policy_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.frozen(root, policy_id=policy_id)
                self.assert_preflight_refuses(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); plan = self.frozen(root)
            doc = json.loads(plan.read_text()); del doc['provenance']['admissionPolicyId']
            plan.write_text(json.dumps(doc))
            (root / 'evaluation-freeze-01.json').write_text(json.dumps(dict(files=[identity(plan)])))
            self.assert_preflight_refuses(root)

    def test_wrong_episode_and_frozen_wrong_threshold_refuse_before_probes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.frozen(root, episode='context-sources-03')
            self.assert_preflight_refuses(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); policy = dict(a.POLICY); policy['minimumFreePercent'] = 19
            self.frozen(root, policy=policy)
            self.assert_preflight_refuses(root)

    def test_unreadable_plan_freeze_or_missing_policy_fail_closed(self):
        for kind in ('missing-plan', 'malformed-plan', 'missing-freeze', 'malformed-freeze', 'missing-policy'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); plan = self.frozen(root); freeze = root / 'evaluation-freeze-01.json'
                if kind == 'missing-plan': plan.unlink()
                elif kind == 'missing-freeze': freeze.unlink()
                elif kind == 'malformed-freeze': freeze.write_text('{')
                elif kind == 'malformed-plan':
                    plan.write_text('{'); freeze.write_text(json.dumps(dict(files=[identity(plan)])))
                else:
                    doc = json.loads(plan.read_text()); del doc['provenance']['hostAdmission']
                    plan.write_text(json.dumps(doc)); freeze.write_text(json.dumps(dict(files=[identity(plan)])))
                self.assert_preflight_refuses(root, (ValueError, KeyError, FileNotFoundError))

    def test_probe_exceptions_are_retained_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.frozen(root)
            returns = [OSError('synthetic unreadable probe'),
                       a.subprocess.TimeoutExpired(a.COMMANDS[1], 10),
                       SimpleNamespace(returncode=0, stdout=samples()[2]['stdout'], stderr='')]
            with patch.object(a.subprocess, 'run', side_effect=returns) as run, \
                 patch.object(a.shutil, 'disk_usage', return_value=SimpleNamespace(free=8 * 1024**3)), \
                 contextlib.redirect_stdout(io.StringIO()):
                a.main(root)
            doc = json.loads((root / 'host-admission-01.json').read_text())
            self.assertFalse(doc['admitted'])
            self.assertIn('error', doc['results'][0]); self.assertIn('error', doc['results'][1])
            self.assertEqual(run.call_count, 3)


if __name__ == '__main__':
    unittest.main()
