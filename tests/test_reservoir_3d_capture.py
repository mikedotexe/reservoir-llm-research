"""Check evidence joins and source-derived controller arithmetic, without live reads."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / 'probes/reservoir_3d_capture.py'
spec = importlib.util.spec_from_file_location('reservoir_3d_capture', PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def record(table, tick, fill=.6, session=1, start=1000):
    payload = {'id': 1, 'session_id': session, 'timestamp': tick}
    if table == 'eigenvalue_timeline':
        payload.update(fill_ratio=fill, lambda1=4, lambda2=2, lambda3=1)
    else:
        payload.update(esn_eig1=20, esn_geom_radius=.4, esn_geom_rel=1,
                       esn_leak=.65, esn_lambda=.97)
    return {'kind': 'telemetry', 'being': 'minime', 'source_record_id': f'{table}:{tick}',
            'occurred_at': start + tick, 'payload': payload,
            'source': {'sha256': probe.digest(probe.encoded(payload)),
                       'locator': {'table': table, 'session': {'start_time': start}}}}


class CaptureTests(unittest.TestCase):
    def test_exact_tick_join_and_rate(self):
        evidence = {'records': [record('eigenvalue_timeline', 1), record('esn_metrics', 1),
                                record('eigenvalue_timeline', 3, .64), record('esn_metrics', 3.0001)]}
        samples, stats = probe.historical_samples(evidence)
        self.assertEqual(stats['n_exact_pairs'], 1)
        self.assertEqual(samples[0]['geom_radius'], .4)
        self.assertIsNone(samples[1]['geom_radius'])
        self.assertIsNone(samples[0]['fill_rate_pct_per_s'])
        self.assertEqual(samples[1]['fill_rate_pct_per_s'], 2)

    def test_no_rate_across_session_boundary(self):
        evidence = {'records': [record('eigenvalue_timeline', 1),
                                record('eigenvalue_timeline', 2, .9, session=2)]}
        samples, _ = probe.historical_samples(evidence)
        self.assertIsNone(samples[1]['fill_rate_pct_per_s'])

    def test_rejects_modified_payload_and_conflicting_clock(self):
        original = record('eigenvalue_timeline', 1)
        altered = deepcopy(original)
        altered['payload']['fill_ratio'] = .8
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            probe.historical_samples({'records': [altered]})
        altered = deepcopy(original)
        altered['occurred_at'] += 1
        with self.assertRaisesRegex(ValueError, 'wall-time conversion'):
            probe.historical_samples({'records': [altered]})

    def test_controller_uses_its_error_not_later_snapshot_fill(self):
        cfg = {'deadband_pct': 4, 'kp': .55, 'ki': .04, 'max_output': .12}
        state = {'fill_pct': 61, 'stable_core': {'structural_pi': {
            'active': True, 'target_fill_pct': 68, 'error_pct': 5, 'integral': .5}}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'health.json'
            path.write_text(json.dumps(state))
            result = probe.controller_snapshot(path, cfg)['derived']
            self.assertEqual(result['controller_input_fill_pct'], 73)
            self.assertEqual(result['snapshot_minus_controller_fill_pct'], -12)
            self.assertEqual(result['p_term'], .0275)
            self.assertEqual(result['i_term'], .02)
            self.assertEqual(result['pi_output'], .0475)
            state['stable_core']['structural_pi']['recovery_impulse_active'] = True
            path.write_text(json.dumps(state))
            self.assertIsNone(probe.controller_snapshot(path, cfg)['derived'])


if __name__ == '__main__':
    unittest.main()
