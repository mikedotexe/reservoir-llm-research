"""Pure/mocked admission checks: no host queries, service or model actions."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import admit_once as a


def samples(free=30, pressure=1):
    return [dict(exit=0, stdout='68719476736\n'), dict(exit=0, stdout=f'{pressure}\n'),
            dict(exit=0, stdout=f'System-wide memory free percentage: {free}%\n')]


class AdmissionTests(unittest.TestCase):
    def test_29_refused_30_and_31_accepted_35_still_accepted(self):
        for free, expected in ((29, False), (30, True), (31, True), (35, True)):
            with self.subTest(free=free):
                self.assertEqual(a.decision(samples(free), 8 * 1024**3, a.POLICY)['admitted'], expected)

    def test_non_normal_pressure_still_refused(self):
        for level in (0, 2, 4):
            self.assertFalse(a.decision(samples(80, level), 100 * 1024**3, a.POLICY)['admitted'])

    def test_disk_boundary_is_unchanged(self):
        self.assertFalse(a.decision(samples(), 8 * 1024**3 - 1, a.POLICY)['admitted'])
        self.assertTrue(a.decision(samples(), 8 * 1024**3, a.POLICY)['admitted'])

    def test_missing_failed_or_malformed_probe_refuses(self):
        cases = [[], samples()[:2]]
        for index in range(3):
            x = samples(); x[index] = dict(error='synthetic timeout'); cases.append(x)
            x = samples(); x[index]['exit'] = 1; cases.append(x)
            x = samples(); x[index]['stdout'] = 'unrecognized'; cases.append(x)
        for x in cases:
            self.assertFalse(a.decision(x, 8 * 1024**3, a.POLICY)['admitted'])

    def test_out_of_range_duplicate_percentage_and_zero_ram_refuse(self):
        for text in ('System-wide memory free percentage: 101%',
                     'System-wide memory free percentage: -1%',
                     'System-wide memory free percentage: 30%\nSystem-wide memory free percentage: 70%'):
            x = samples(); x[2]['stdout'] = text
            self.assertFalse(a.decision(x, 8 * 1024**3, a.POLICY)['admitted'])
        x = samples(); x[0]['stdout'] = '0'
        self.assertFalse(a.decision(x, 8 * 1024**3, a.POLICY)['admitted'])

    def test_changed_policy_not_silently_applied(self):
        for key, value in (('minimumFreePercent', 29), ('requiredPressureLevel', 2),
                           ('minimumFreeDiskBytes', 1), ('attempts', 2)):
            policy = dict(a.POLICY); policy[key] = value
            with self.assertRaisesRegex(ValueError, 'policy'):
                a.decision(samples(), 8 * 1024**3, policy)

    def frozen(self, root, policy=None):
        plan = dict(episodeId='context-sources-03', provenance=dict(
            hostAdmission=policy or a.POLICY, admissionPolicyId='normal-pressure-reported-free-30-v1'))
        raw = (json.dumps(plan) + '\n').encode(); path = root / 'run-plan.json'; path.write_bytes(raw)
        ref = dict(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        (root / 'evaluation-freeze-01.json').write_text(json.dumps(dict(files=[ref])))
        return path

    def test_real_entrypoint_uses_approved_boundary_and_records_policy(self):
        for free, expected in ((29, False), (30, True), (31, True)):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.frozen(root)
                returns = [SimpleNamespace(returncode=x['exit'], stdout=x['stdout'], stderr='') for x in samples(free)]
                with patch.object(a.subprocess, 'run', side_effect=returns) as run, \
                     patch.object(a.shutil, 'disk_usage', return_value=SimpleNamespace(free=8 * 1024**3)):
                    a.main(root)
                doc = json.loads((root / 'host-admission-01.json').read_text())
                self.assertEqual(doc['admitted'], expected); self.assertEqual(doc['thresholds'], a.POLICY)
                self.assertEqual(doc['totalMemoryBytes'], 68719476736)
                self.assertEqual([c.args[0] for c in run.call_args_list], list(a.COMMANDS))

    def test_existing_even_partial_receipt_prevents_any_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'host-admission-01.json').write_text('')
            with patch.object(a.subprocess, 'run') as run, patch.object(a.shutil, 'disk_usage') as disk:
                with self.assertRaises(FileExistsError): a.main(root)
            run.assert_not_called(); disk.assert_not_called()

    def test_changed_plan_or_unbound_policy_stops_before_any_probe(self):
        for changed in (True, False):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); path = self.frozen(root)
                if changed:
                    path.write_text(path.read_text() + ' ')
                else:
                    policy = dict(a.POLICY); policy['minimumFreePercent'] = 29; self.frozen(root, policy)
                with patch.object(a.subprocess, 'run') as run, patch.object(a.shutil, 'disk_usage') as disk:
                    with self.assertRaises(ValueError): a.main(root)
                run.assert_not_called(); disk.assert_not_called()
                self.assertTrue((root / 'host-admission-01.json').exists())


if __name__ == '__main__':
    unittest.main()
