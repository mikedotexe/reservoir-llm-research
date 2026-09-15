"""Validate measured-state geometry and bounded capture using synthetic inputs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

PATH = Path(__file__).resolve().parents[1] / 'probes/reservoir_3d_state_geometry.py'
spec = importlib.util.spec_from_file_location('state_geometry_probe', PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class StateGeometryTests(unittest.TestCase):
    def test_known_spectrum_exact_normalization_and_mean(self):
        # Orthogonal sign patterns yield an exact diagonal centered covariance.
        a = np.array([[1, 1, 1, 1], [1, 1, -1, -1], [1, -1, 1, -1],
                      [1, -1, -1, 1], [-1, 1, 1, -1], [-1, 1, -1, 1],
                      [-1, -1, 1, 1], [-1, -1, -1, -1]], dtype=float)
        state = a * [4, 3, 2, 1] + [2, -1, 7, 5]
        pca, rows = probe.analyze(state)
        np.testing.assert_allclose(pca['eigenvalues'], np.array([16, 9, 4, 1]) * 8 / 7)
        np.testing.assert_allclose(pca['mean'], [2, -1, 7, 5])
        self.assertAlmostEqual(pca['retained_fraction'], 29 / 30)
        self.assertAlmostEqual(sum(pca['explained_variance_ratio']), 1)
        self.assertAlmostEqual(pca['relative_reconstruction_error'] ** 2, 1 / 30)
        for row in rows:
            self.assertAlmostEqual(row['centered_norm'] ** 2,
                                   row['projected_norm'] ** 2 + row['residual_norm'] ** 2)

    def test_rotation_preserves_spectrum_and_reconstruction(self):
        rng = np.random.default_rng(132)
        states = rng.normal(size=(40, 9)) * np.arange(1, 10)
        rotation, _ = np.linalg.qr(rng.normal(size=(9, 9)))
        first, _ = probe.analyze(states)
        rotated, _ = probe.analyze(states @ rotation)
        np.testing.assert_allclose(first['eigenvalues'], rotated['eigenvalues'])
        self.assertAlmostEqual(first['retained_fraction'], rotated['retained_fraction'])
        self.assertLess(first['checks']['component_orthogonality_max_error'], 1e-12)

    def test_rejects_invalid_binary_dimensions_and_nonfinite_states(self):
        meta = {'dtype': '<f4', 'layout': 'row_major', 'esn_window_rows': 2,
                'esn_window_cols': 3, 'esn_n': 3}
        with self.assertRaisesRegex(ValueError, 'byte size'):
            probe.validate_states(b'123', meta)
        state = np.zeros((2, 3), dtype='<f4')
        state[1, 1] = np.nan
        with self.assertRaisesRegex(ValueError, 'non-finite'):
            probe.validate_states(state.tobytes(), meta)
        with self.assertRaisesRegex(ValueError, 'zero temporal variance'):
            probe.analyze(np.ones((5, 3)))

    def test_stable_snapshot_preserves_exact_input_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = np.arange(12, dtype='<f4').tobytes()
            meta_raw = json.dumps({'dtype': '<f4', 'layout': 'row_major',
                                  'esn_window_rows': 4, 'esn_window_cols': 3,
                                  'esn_n': 3, 't_ms': 123}).encode()
            (root / 'esn_state_window.bin').write_bytes(raw)
            (root / 'capacity_dump_meta.json').write_bytes(meta_raw)
            captured, captured_meta, source = probe.capture(root, settle_seconds=0)
            self.assertEqual(captured, raw)
            self.assertEqual(captured_meta, meta_raw)
            self.assertEqual(source['files']['states']['sha256'], probe.digest(raw))
            self.assertFalse(source['consistency']['producer_transactional_pair_guarantee'])

    def test_moved_replay_uses_hash_verified_local_snapshot_without_rewriting_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b'retained state bytes'
            name = f'captured-states-{probe.digest(raw)[:16]}.bin'
            source = {'files': {'states': {'snapshot_path': str(root / 'old' / name),
                                          'sha256': probe.digest(raw)}}}
            before = json.dumps(source)
            (root / name).write_bytes(raw)
            self.assertEqual(probe.read_replay_snapshot(root / 'export.json', source, 'states', 100), raw)
            self.assertEqual(json.dumps(source), before)
            (root / name).write_bytes(b'changed bytes')
            with self.assertRaisesRegex(ValueError, 'snapshot hash mismatch'):
                probe.read_replay_snapshot(root / 'export.json', source, 'states', 100)

    def test_existing_recorded_snapshot_tamper_cannot_fall_back_to_valid_local_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b'retained state bytes'
            original = root / 'original' / 'snapshot.bin'
            original.parent.mkdir()
            original.write_bytes(raw)
            (root / original.name).write_bytes(raw)
            source = {'files': {'states': {'snapshot_path': str(original),
                                          'sha256': probe.digest(raw)}}}
            self.assertEqual(probe.read_replay_snapshot(root / 'export.json', source, 'states', 100), raw)
            original.write_bytes(b'changed original')
            with self.assertRaisesRegex(ValueError, 'snapshot hash mismatch'):
                probe.read_replay_snapshot(root / 'export.json', source, 'states', 100)

    def test_relative_replay_snapshot_is_resolved_beside_export_and_remains_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b'retained state bytes'
            source = {'files': {'states': {'snapshot_path': 'snapshot.bin',
                                          'sha256': probe.digest(raw)}}}
            (root / 'snapshot.bin').write_bytes(raw)
            self.assertEqual(probe.read_replay_snapshot(root / 'export.json', source, 'states', 100), raw)
            with self.assertRaisesRegex(ValueError, 'Bounded read exceeds'):
                probe.read_replay_snapshot(root / 'export.json', source, 'states', 4)


if __name__ == '__main__':
    unittest.main()
