"""Synthetic analysis/admission checks only; no host/process/libproc calls."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('owned_app_sampler', Path(__file__).with_name('sample_owned_app.py'))
SAMPLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SAMPLER)


def marker(phase, seconds):
    return {'phase': phase, 'monotonicNs': str(int(seconds * 1e9))}


def sample(at, start=None, cpu=0, rss=100, sequence=0):
    return {'type': 'sample', 'sequence': sequence, 'monotonicNs': str(int(at * 1e9)), 'errors': [],
            'process': {'identityVerified': True, 'rssBytes': rss, 'threadCount': 3, 'fdCount': 4,
                        'cpuIntervalStartMonotonicNs': None if start is None else str(int(start * 1e9)),
                        'cpuDeltaNanoseconds': None if start is None else str(int(cpu * 1e9))}}


def records(samples, footer=True):
    rows = [{'type': 'header', 'schema': SAMPLER.SCHEMA, 'process': {'executableSha256': 'a' * 64}}] + samples
    if footer:
        rows.append({'type': 'footer', 'status': 'completed', 'sampleCount': len(samples),
                     'finalExecutableSha256': 'a' * 64, 'errors': []})
    return rows


class AnalysisTests(unittest.TestCase):
    def test_phase_crossing_cpu_is_excluded(self):
        result = SAMPLER.analyze_rows(records([sample(10, 5, 1), sample(15, 10, .5)]),
                                     [marker('visible-idle', 8), marker('end', 16)])
        window = result['windows'][0]
        self.assertEqual(window['cpuIntervalCount'], 1)
        self.assertEqual(window['cpuCoveredSeconds'], 5)
        self.assertEqual(window['cpuWeightedPercent'], 10)

    def test_cpu_uses_duration_weighting_not_sample_mean(self):
        result = SAMPLER.analyze_rows(records([sample(2, 0, 1), sample(7, 2, .5)]),
                                     [marker('playback', 0), marker('end', 8)])
        self.assertAlmostEqual(result['windows'][0]['cpuWeightedPercent'], 100 * 1.5 / 7)
        self.assertNotEqual(result['windows'][0]['cpuWeightedPercent'], 30)

    def test_missed_row_does_not_bridge_cpu_or_hide_errors(self):
        missing = sample(5, sequence=1)
        missing['process'] = None
        missing['errors'] = [{'component': 'process', 'errno': 3}]
        rows = records([sample(0), missing, sample(10, 0, 5, sequence=2), sample(15, 10, .1, sequence=3)])
        result = SAMPLER.analyze_rows(rows, [marker('minimized', 0), marker('end', 16)])
        self.assertEqual(result['windows'][0]['cpuIntervalCount'], 1)
        self.assertEqual(result['windows'][0]['cpuWeightedPercent'], 2)
        self.assertEqual(result['allSampleErrors'][0]['errors'], missing['errors'])

    def test_unclosed_phase_and_incomplete_capture_remain_explicit(self):
        result = SAMPLER.analyze_rows(records([sample(5, 0, 1)], footer=False), [marker('restored-idle', 0)])
        self.assertFalse(result['windows'][0]['closed'])
        self.assertIsNone(result['windows'][0]['cpuWeightedPercent'])
        self.assertIn('Missing terminal footer', result['issues'][0])

    def test_settling_is_not_a_measurement_window(self):
        result = SAMPLER.analyze_rows(records([sample(5, 0, 5), sample(20, 15, .1)]),
                                     [marker('settling', 0), marker('visible-idle', 15), marker('end', 21)])
        self.assertEqual(len(result['windows']), 1)
        self.assertEqual(result['windows'][0]['cpuWeightedPercent'], 2)

    def test_hash_change_and_terminal_failure_are_not_qualified(self):
        rows = records([sample(0)])
        rows[-1].update(status='capture-failed', finalExecutableSha256='b' * 64)
        result = SAMPLER.analyze_rows(rows, [marker('visible-idle', 0), marker('end', 60)])
        self.assertIn('Capture did not finish normally', result['issues'])
        self.assertIn('Final executable identity not confirmed', result['issues'])

    def test_invalid_markers_rejected(self):
        for markers in ([marker('unknown', 0)], [marker('playback', 5), marker('end', 5)]):
            with self.assertRaises(ValueError):
                SAMPLER.analyze_rows(records([sample(0)]), markers)

    def test_nonfinite_missing_or_boolean_point_metrics_excluded(self):
        samples = [sample(0, rss=float('nan')), sample(5, rss=True), sample(10, rss=None), sample(15, rss=200)]
        result = SAMPLER.analyze_rows(records(samples), [marker('visible-idle', 0), marker('end', 60)])
        self.assertEqual(result['windows'][0]['metrics']['rssBytes'], {'count': 1, 'minimum': 200, 'median': 200, 'maximum': 200})


class NoRuntimeAdmissionTests(unittest.TestCase):
    def test_wrong_launch_hash_refuses_before_loading_libproc(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'launch.json'
            path.write_text(json.dumps({'pid': 123, 'executable': 'never-opened'}))
            args = argparse.Namespace(duration_seconds=600, launch_receipt=path, expected_launch_sha256='0' * 64)
            with patch.object(SAMPLER, 'load_metrics') as load:
                with self.assertRaisesRegex(ValueError, 'receipt hash mismatch'):
                    SAMPLER.capture(args)
                load.assert_not_called()

    def test_duration_ceiling_refuses_before_file_or_host_access(self):
        args = argparse.Namespace(duration_seconds=601)
        with patch.object(SAMPLER, 'load_metrics') as load:
            with self.assertRaisesRegex(ValueError, '600'):
                SAMPLER.capture(args)
            load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
